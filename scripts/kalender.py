#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Holt die Termine aus der Vereins-API und schreibt sie in die Website.

Aufruf:  python3 scripts/kalender.py <URL zur open_events.json>

Die Adresse der eigenen Website steht in der Umgebungsvariablen SITE_URL; sie
landet in den Abo-Links. Ohne sie greift STANDARD_SITE_URL.

Erwartetes Format:
    {"semester": "WS 26/27",
     "scheduled_events": [{"name": ..., "place": ..., "date": [start, ende]}, ...],
     "other_events": ["Fuchsenabende", ...]}

Zeitangaben kommen als "MM/DD/YYYY HH:MM:SS" in Ortszeit.

Geschrieben werden data/termine.json (Rohdaten), termine.ics (abonnierbarer
Kalender) und vier Bereiche in veranstaltungen.html, jeweils zwischen Markern.
Dadurch steht die Liste direkt im Quelltext: ohne JavaScript sichtbar und fuer
Suchmaschinen lesbar.

Bewusst ohne Fremdbibliotheken, damit die Action nichts installieren muss.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from hashlib import sha1
from html import escape

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
          "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
HTML_DATEI = "veranstaltungen.html"
JSON_DATEI = "data/termine.json"
ICS_DATEI = "termine.ics"
MAX_TERMINE = 12
# Termine ohne Ende bekommen im Kalender diese Dauer, sonst zeigen viele Apps
# einen Eintrag von null Minuten an.
STANDARDDAUER_STUNDEN = 2
# Fallback, falls die Action keine SITE_URL mitgibt. Ohne absolute Adresse
# waere der Abo-Link wertlos: Kalender-Apps rufen ihn von aussen ab.
STANDARD_SITE_URL = "https://alaeubli.github.io/ftv-Hohenstaufen"

# Die Schnittstelle liefert den Ort mal als "adH", mal als vollstaendige
# Anschrift, mal gar nicht. Auf der Seite soll dafuer immer dasselbe stehen.
# Es gibt vier Faelle:
#   eigenes Haus -> "Hohenstaufenhaus, Mozartstrasse 31". Bewusst die Adresse
#                   und nicht "auf dem Haus": wer noch nie da war, kann mit
#                   dem Verbindungsjargon nichts anfangen.
#   online       -> "Online". Im Kalender bleibt stehen, was eingetragen war,
#                   damit ein Einwahllink dort anklickbar ist.
#   fremder Ort  -> so uebernehmen, wie er kommt, nur ohne ", Deutschland"
#   leeres Feld  -> leer lassen; beim Termin steht dann gar kein Ort, statt
#                   dass wir einen erfinden und Gaeste vor der falschen Tuer
#                   stehen
HAUS_KURZ = "Hohenstaufenhaus, Mozartstraße 31"
HAUSANSCHRIFT = "Hohenstaufenhaus, Mozartstraße 31, 73430 Aalen"
ONLINE = "Online"
# Schreibweisen, die alle das eigene Haus meinen. Verglichen wird klein-
# geschrieben und ohne Punkte, "adH" und "AdH." landen also beide hier.
EIGENES_HAUS = {
    "adh", "auf dem haus", "auf dem hause", "aufm haus", "im haus", "haus",
    "zuhause", "daheim", "hohenstaufenhaus", "hohenstaufen-haus",
    "verbindungshaus",
}
# Faengt jede Schreibweise der eigenen Strasse ab: "Mozartstr. 31",
# "Mozartstrasse 31, 73430 Aalen", "Mozartstrasse 31, Aalen, Deutschland".
EIGENE_STRASSE = re.compile(r"mozartstr(?:asse)?\s*31\b")
# Online-Termine erkennt das Skript am Ort, nie am Titel: ein "Webinar" kann
# sehr wohl gemeinsam im Kneipsaal geschaut werden, und dann ist der Ort das
# Haus. Wer einen Termin in Gaudeam als "Online" oder mit Einwahllink
# eintraegt, bekommt hier "Online".
ONLINE_WORTE = ("online", "zoom", "teams", "webex", "bigbluebutton", "jitsi",
                "discord", "skype", "meet.google", "gotomeeting",
                "videokonferenz", "videocall", "remote")
ONLINE_LINK = re.compile(r"https?://")
# Ein Kartenlink ist kein Einwahllink, sondern ein sehr realer Ort.
KARTEN_LINK = re.compile(r"(google\.[a-z.]+/maps|goo\.gl/maps|maps\.app\.goo\.gl"
                         r"|openstreetmap|apple\.com/maps|osm\.org)")


def zeit(rohwert):
    """'10/17/2026 19:00:00' -> datetime. Steht an erster Stelle eine Zahl
    groesser als zwoelf, wird das Feld als Tag gelesen; das faengt einen
    Wechsel auf das deutsche Format ab, ohne dass etwas stillschweigend
    um Monate verrutscht."""
    roh = (rohwert or "").strip()
    if not roh:
        raise ValueError("leere Zeitangabe")
    datum, _, uhr = roh.partition(" ")
    teile = datum.split("/")
    if len(teile) != 3:
        raise ValueError("unbekanntes Datumsformat: %r" % roh)
    a, b, jahr = (int(t) for t in teile)
    monat, tag = (b, a) if a > 12 else (a, b)
    stunde, minute, sekunde = 0, 0, 0
    if uhr:
        werte = [int(x) for x in uhr.split(":")[:3]]
        stunde, minute, sekunde = (werte + [0, 0, 0])[:3]
    return datetime(jahr, monat, tag, stunde, minute, sekunde)


def ort_saeubern(roh):
    """Vereinheitlicht Leerzeichen und schneidet das ", Deutschland" ab, das
    die Schnittstelle an vollstaendige Anschriften haengt."""
    text = re.sub(r"\s+", " ", (roh or "").strip())
    text = re.sub(r",?\s*Deutschland\.?$", "", text, flags=re.I)
    return text.strip(" ,.").strip()


def ist_eigenes_haus(roh):
    """Erkennt alle Schreibweisen des eigenen Hauses, damit derselbe Ort nicht
    einmal als "adH" und einmal als Anschrift auf der Seite steht."""
    schluessel = ort_saeubern(roh).lower().replace("\u00df", "ss").replace(".", "")
    schluessel = re.sub(r"\s+", " ", schluessel).strip()
    if not schluessel:
        return False
    return schluessel in EIGENES_HAUS or bool(EIGENE_STRASSE.search(schluessel))


def ist_online(roh):
    """Erkennt einen Online-Termin am Ort. Der Titel wird bewusst nicht
    herangezogen: ein Vortrag kann online stattfinden oder gemeinsam im Haus
    geschaut werden, und das steht nur im Ortsfeld."""
    text = ort_saeubern(roh).lower()
    if not text:
        return False
    if ONLINE_LINK.search(text) and not KARTEN_LINK.search(text):
        return True
    return any(wort in text for wort in ONLINE_WORTE)


def ort_lesbar(roh):
    """Fuer die Website. Ein leeres Feld bleibt leer, dann faellt die Ortszeile
    beim Termin ganz weg."""
    if ist_eigenes_haus(roh):
        return HAUS_KURZ
    if ist_online(roh):
        return ONLINE
    return ort_saeubern(roh)


def ort_kalender(roh):
    """Fuer die Kalenderdatei. Dort landet der Ort in der Navigation, deshalb
    fuers eigene Haus die Anschrift mit Postleitzahl. Bei Online-Terminen
    bleibt stehen, was eingetragen war: ein Einwahllink ist im Kalender
    anklickbar, "Online" waere dort verschenkt."""
    if ist_eigenes_haus(roh):
        return HAUSANSCHRIFT
    return ort_saeubern(roh)


def uhrzeit_text(start, ende):
    """Zeigt eine Spanne, wenn Anfang und Ende am selben Tag liegen."""
    if ende and ende.date() == start.date() and ende > start:
        return "%s bis %s Uhr" % (start.strftime("%H:%M"), ende.strftime("%H:%M"))
    return "%s Uhr" % start.strftime("%H:%M")


def termine_lesen(daten):
    eintraege, uebersprungen = [], []
    for roh in daten.get("scheduled_events") or []:
        name = (roh.get("name") or "").strip()
        datumsfeld = roh.get("date") or []
        if isinstance(datumsfeld, str):
            datumsfeld = [datumsfeld]
        if not name or not datumsfeld:
            uebersprungen.append(name or "(ohne Namen)")
            continue
        try:
            start = zeit(datumsfeld[0])
            ende = zeit(datumsfeld[1]) if len(datumsfeld) > 1 and datumsfeld[1] else None
        except (ValueError, TypeError) as fehler:
            uebersprungen.append("%s (%s)" % (name, fehler))
            continue
        eintraege.append({"start": start, "ende": ende, "name": name,
                          "ort": ort_lesbar(roh.get("place")),
                          "ort_ics": ort_kalender(roh.get("place")),
                          "online": ist_online(roh.get("place"))})
    return eintraege, uebersprungen


# Die Ortszeile einer Terminkarte. Steht separat, weil sie entfaellt,
# wenn zu einem Termin kein Ort bekannt ist.
ORTZEILE = ('<span class="flex items-center gap-2 min-w-0">'
            '<svg aria-hidden="true" class="text-primary flex-shrink-0 w-[18px] h-[18px]" '
            'fill="currentColor" viewBox="0 -960 960 960"><path d="M480.09-490q28.91 0 49.41-20.59 '
            '20.5-20.59 20.5-49.5t-20.59-49.41q-20.59-20.5-49.5-20.5t-49.41 20.59q-20.5 20.59-20.5 '
            '49.5t20.59 49.41q20.59 20.5 49.5 20.5ZM480-159q133-121 196.5-219.5T740-552q0-117.79-75.29-192.9Q589.42-820 '
            '480-820t-184.71 75.1Q220-669.79 220-552q0 75 65 173.5T480-159Zm0 79Q319-217 239.5-334.5T160-552q0-150 '
            '96.5-239T480-880q127 0 223.5 89T800-552q0 100-79.5 217.5T480-80Zm0-480Z"/></svg>'
            '<span class="min-w-0 break-words">%s</span></span>')
# Dieselbe Zeile fuer Online-Termine, nur mit Kamera statt Stecknadel.
ONLINEZEILE = ('<span class="flex items-center gap-2 min-w-0">'
               '<svg aria-hidden="true" class="text-primary flex-shrink-0 w-[18px] h-[18px]" '
               'fill="currentColor" viewBox="0 -960 960 960"><path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 '
               '23.5-56.5T160-800h480q33 0 56.5 23.5T720-720v180l160-160v520L720-340v100q0 33-23.5 '
               '56.5T640-160H160Zm0-60h480v-480H160v480Z"/></svg>'
               '<span class="min-w-0 break-words">%s</span></span>')


def liste_bauen(eintraege):
    if not eintraege:
        return ('<p class="font-body-md text-body-md text-on-surface-variant text-center">'
                'Gerade steht nichts an. Schau bald wieder vorbei oder frag uns kurz '
                'per WhatsApp, was als Nächstes läuft.</p>')
    teile = []
    for e in eintraege:
        d = e["start"]
        # Ohne Ort keine Ortszeile: eine Stecknadel ohne Text daneben sieht
        # nach einem Fehler aus.
        ort = ""
        if e["ort"]:
            vorlage = ONLINEZEILE if e.get("online") else ORTZEILE
            ort = ("\n" + vorlage) % escape(e["ort"])
        teile.append('''<article class="flex gap-4 sm:gap-6 items-start sm:items-center bg-surface-container-lowest rounded-xl border border-surface-container p-4 sm:p-6 shadow-[0_10px_30px_rgba(32,89,48,0.03)] hover:shadow-[0_15px_40px_rgba(32,89,48,0.06)] hover:-translate-y-0.5 transition-all duration-300">
<div class="flex-shrink-0 flex flex-col items-center justify-center w-14 h-14 sm:w-20 sm:h-20 bg-secondary-container rounded-lg">
<span class="font-display-lg text-body-lg sm:text-headline-md font-semibold text-primary leading-none">{tag:02d}</span>
<span class="font-label-sm text-label-sm uppercase text-primary mt-1">{monat}</span>
</div>
<div class="flex-1 min-w-0">
<h3 class="font-headline-md text-body-lg sm:text-headline-md text-on-surface mb-stack-sm break-words">{titel}</h3>
<div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-1 sm:gap-x-6 font-body-md text-body-md text-on-surface-variant">
<span class="flex items-center gap-2 min-w-0"><svg aria-hidden="true" class="text-primary flex-shrink-0 w-[18px] h-[18px]" fill="currentColor" viewBox="0 -960 960 960"><path d="m627-287 45-45-159-160v-201h-60v225l174 181ZM480-80q-82 0-155-31.5t-127.5-86Q143-252 111.5-325T80-480q0-82 31.5-155t86-127.5Q252-817 325-848.5T480-880q82 0 155 31.5t127.5 86Q817-708 848.5-635T880-480q0 82-31.5 155t-86 127.5Q708-143 635-111.5T480-80Zm0-400Zm0 340q140 0 240-100t100-240q0-140-100-240T480-820q-140 0-240 100T140-480q0 140 100 240t240 100Z"/></svg>{uhrzeit}</span>{ort}
</div>
</div>
</article>'''.format(tag=d.day, monat=MONATE[d.month - 1],
                     titel=escape(e["name"]),
                     uhrzeit=escape(uhrzeit_text(d, e["ende"])),
                     ort=ort))
    return "\n".join(teile)


def sonstiges_bauen(namen):
    namen = [n.strip() for n in (namen or []) if n and n.strip()]
    if not namen:
        return ""
    aufzaehlung = escape(namen[0]) if len(namen) == 1 else \
        "%s und %s" % (", ".join(escape(n) for n in namen[:-1]), escape(namen[-1]))
    return ('<div class="mt-stack-lg bg-surface-container-low rounded-xl p-6 flex flex-col '
            'sm:flex-row sm:items-center gap-4">\n'
            '<svg aria-hidden="true" class="text-primary flex-shrink-0 w-6 h-6" fill="currentColor" viewBox="0 -960 960 960"><path d="M207.86-432Q188-432 174-446.14t-14-34Q160-500 174.14-514t34-14Q228-528 242-513.86t14 34Q256-460 241.86-446t-34 14Zm272 0Q460-432 446-446.14t-14-34Q432-500 446.14-514t34-14Q500-528 514-513.86t14 34Q528-460 513.86-446t-34 14Zm272 0Q732-432 718-446.14t-14-34Q704-500 718.14-514t34-14Q772-528 786-513.86t14 34Q800-460 785.86-446t-34 14Z"/></svg>\n'
            '<p class="font-body-md text-body-md text-on-surface-variant">Dazu kommen über das '
            'Semester verteilt %s. Die Termine dafür stehen noch nicht fest, frag uns einfach '
            'kurz per WhatsApp.</p>\n</div>' % aufzaehlung)


# --- Kalenderdatei -----------------------------------------------------------
# Bewusst von Hand gebaut statt mit einer Bibliothek, damit die Action nichts
# installieren muss. Die Regeln stehen in RFC 5545.

# Die Termine kommen ohne Zeitzone, gemeint ist immer Ortszeit. Damit ein Abo
# aus dem Ausland nicht um Stunden verrutscht, wird die Zone mitgeliefert. Die
# Umstellungsregeln fuer Europe/Berlin gelten unveraendert seit 1996.
VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Berlin
X-LIC-LOCATION:Europe/Berlin
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def ics_text(wert):
    """Backslash, Semikolon, Komma und Zeilenumbrueche haben in einer
    Kalenderdatei eine Bedeutung und muessen maskiert werden."""
    return (str(wert).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))


def ics_falten(zeile):
    """RFC 5545 erlaubt hoechstens 75 Oktette je Zeile. Gezaehlt wird in
    Bytes, nicht in Zeichen: ein Umlaut belegt in UTF-8 zwei davon."""
    roh = zeile.encode("utf-8")
    if len(roh) <= 75:
        return zeile
    stuecke, rest = [], roh
    grenze = 75
    while len(rest) > grenze:
        schnitt = grenze
        # Nicht mitten in ein Mehrbyte-Zeichen schneiden.
        while schnitt > 0 and (rest[schnitt] & 0xC0) == 0x80:
            schnitt -= 1
        stuecke.append(rest[:schnitt].decode("utf-8"))
        rest = rest[schnitt:]
        grenze = 74  # Folgezeilen beginnen mit einem Leerzeichen.
    stuecke.append(rest.decode("utf-8"))
    return "\r\n ".join(stuecke)


def ics_uid(eintrag):
    """Aus Titel und Startzeit abgeleitet, damit ein Termin bei jedem Lauf
    dieselbe Kennung behaelt. Sonst wuerde jede Aktualisierung im Abo als
    neuer Termin erscheinen und der alte bliebe stehen."""
    kern = "%s|%s" % (eintrag["start"].strftime("%Y%m%dT%H%M%S"), eintrag["name"])
    return "%s@hohenstaufen-aalen.de" % sha1(kern.encode("utf-8")).hexdigest()


def ics_bauen(eintraege, semester, zeitstempel):
    zeilen = ["BEGIN:VCALENDAR",
              "VERSION:2.0",
              "PRODID:-//FtV Hohenstaufen zu Aalen//Termine//DE",
              "CALSCALE:GREGORIAN",
              "METHOD:PUBLISH",
              "X-WR-CALNAME:FtV Hohenstaufen zu Aalen",
              "X-WR-TIMEZONE:Europe/Berlin",
              "X-WR-CALDESC:Termine der Forstlich-technischen Verbindung "
              "Hohenstaufen zu Aalen%s" % (" (%s)" % semester if semester else ""),
              # Bitte an die Kalender-App, nicht oefter als stuendlich nachzusehen.
              "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
              "X-PUBLISHED-TTL:PT12H"]
    zeilen.extend(VTIMEZONE.split("\n"))
    for e in sorted(eintraege, key=lambda x: x["start"]):
        ende = e["ende"]
        if not ende or ende <= e["start"]:
            ende = e["start"] + timedelta(hours=STANDARDDAUER_STUNDEN)
        zeilen.extend([
            "BEGIN:VEVENT",
            "UID:%s" % ics_uid(e),
            "DTSTAMP:%s" % zeitstempel,
            "DTSTART;TZID=Europe/Berlin:%s" % e["start"].strftime("%Y%m%dT%H%M%S"),
            "DTEND;TZID=Europe/Berlin:%s" % ende.strftime("%Y%m%dT%H%M%S"),
            "SUMMARY:%s" % ics_text(e["name"])])
        # Ohne Ort kein LOCATION-Feld. Ein leeres zeigen manche Apps als
        # Zeile ohne Inhalt an.
        if e["ort_ics"]:
            zeilen.append("LOCATION:%s" % ics_text(e["ort_ics"]))
        zeilen.extend(["STATUS:CONFIRMED", "TRANSP:OPAQUE", "END:VEVENT"])
    zeilen.append("END:VCALENDAR")
    return "\r\n".join(ics_falten(z) for z in zeilen) + "\r\n"


def ics_schreiben(eintraege, semester):
    """Schreibt nur, wenn sich wirklich ein Termin geaendert hat. Der
    Zeitstempel allein zaehlt nicht, sonst entstuende bei jedem Lauf ein
    Commit."""
    def ohne_zeitstempel(text):
        return [z for z in text.splitlines() if not z.startswith("DTSTAMP:")]

    # DTSTAMP steht nach RFC 5545 in UTC. Bewusst datetime.now(timezone.utc)
    # und nicht datetime.utcnow(): das liefert eine Zeit ohne Zone, die nur so
    # tut, als waere sie UTC, und ist deshalb abgekuendigt. timezone.utc statt
    # datetime.UTC, weil letzteres erst ab Python 3.11 existiert.
    jetzt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    neu = ics_bauen(eintraege, semester, jetzt)
    if os.path.exists(ICS_DATEI):
        try:
            with open(ICS_DATEI, encoding="utf-8") as fh:
                alt = fh.read()
            if ohne_zeitstempel(alt) == ohne_zeitstempel(neu):
                print("%s unveraendert." % ICS_DATEI)
                return
        except OSError:
            pass
    with open(ICS_DATEI, "w", encoding="utf-8", newline="") as fh:
        fh.write(neu)
    print("%s aktualisiert (%d Termine)." % (ICS_DATEI, len(eintraege)))


def kalenderlinks_bauen(site_url):
    """Baut die drei Wege in den eigenen Kalender: abonnieren, herunterladen
    und die Adresse zum Selbstkopieren. Alle drei zeigen auf dieselbe
    Datei, unterschiedlich ist nur, was der Client daraus macht."""
    # Der Abo-Knopf traegt "webcal:" mit der vollstaendigen https-Adresse
    # dahinter, also ein Doppelpunkt und keine zwei Schraegstriche. Das ist
    # eine gueltige opake URI: Schema "webcal", Rest der Pfad. Browser lassen
    # sie unveraendert, und eine App, die nur "webcal:" abschneidet, behaelt
    # genau die richtige https-Adresse uebrig.
    #
    # Achtung, zwei Varianten, die NICHT funktionieren:
    #   webcal://https://...  Nach "//" erwartet jeder Parser einen Hostnamen
    #                         und liest dort "https" als Rechnernamen.
    #   webcal://host/pfad    Korrekt nach Norm, aber genau die Form, an der
    #                         abschneidende Apps scheitern ("//host/pfad").
    # Wessen App das Schema stur durch "https:" ersetzt, bekommt hier
    # "https:https://..." und kommt nicht ans Ziel. Fuer die steht die Adresse
    # im Klartext darunter, das ist der Weg, der ueberall geht.
    https = "%s/%s" % (site_url.rstrip("/"), ICS_DATEI)
    webcal = "webcal:%s" % https
    return '''<div class="flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-4">
<a class="bg-primary text-white font-body-md text-body-md font-medium px-8 py-4 rounded-full hover:bg-primary-container hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2 whitespace-nowrap" href="{webcal}">
<svg aria-hidden="true" class="w-6 h-6" fill="currentColor" viewBox="0 -960 960 960"><path d="M596.82-220Q556-220 528-248.18q-28-28.19-28-69Q500-358 528.18-386q28.19-28 69-28Q638-414 666-385.82q28 28.19 28 69Q694-276 665.82-248q-28.19 28-69 28ZM180-80q-24 0-42-18t-18-42v-620q0-24 18-42t42-18h65v-60h65v60h340v-60h65v60h65q24 0 42 18t18 42v620q0 24-18 42t-42 18H180Zm0-60h600v-430H180v430Zm0-490h600v-130H180v130Zm0 0v-130 130Z"/></svg>Kalender abonnieren</a>
<a class="bg-transparent border border-primary text-primary font-body-md text-body-md font-medium px-8 py-4 rounded-full hover:bg-secondary-container transition-colors flex items-center justify-center gap-2 whitespace-nowrap w-full sm:w-auto" download="ftv-hohenstaufen-termine.ics" href="{datei}">
<svg aria-hidden="true" class="w-6 h-6" fill="currentColor" viewBox="0 -960 960 960"><path d="M480-313 287-506l43-43 120 120v-371h60v371l120-120 43 43-193 193ZM220-160q-24 0-42-18t-18-42v-143h60v143h520v-143h60v143q0 24-18 42t-42 18H220Z"/></svg>iCal-Datei laden</a>
</div>
<p class="mt-stack-md font-body-md text-body-md text-on-surface-variant">Passiert beim ersten Knopf nichts oder meldet deine App eine ungültige Adresse, trag diese Adresse dort von Hand als Kalender-Abo ein. Das klappt überall und ist im Google Kalender ohnehin der einzige Weg: <span class="text-on-surface">Weitere Kalender &rarr; Per URL</span>.</p>
<p class="mt-2 font-body-md text-body-md text-primary break-all"><a class="underline underline-offset-4 hover:no-underline" href="{datei}">{datei}</a></p>
<p class="mt-stack-md font-body-md text-body-md text-on-surface-variant">Ein Abo hält sich von allein aktuell. Die heruntergeladene Datei ist dagegen eine Momentaufnahme: einmal eingelesen, erfährt sie von späteren Verschiebungen nichts mehr.</p>'''.format(webcal=escape(webcal, quote=True), datei=escape(https, quote=True))


def ersetzen(seite, marker, inhalt):
    start, ende = "<!-- %s:START -->" % marker, "<!-- %s:END -->" % marker
    if start not in seite or ende not in seite:
        sys.exit("Fehler: Marker %s / %s fehlen in %s." % (start, ende, HTML_DATEI))
    neu = "%s\n%s\n%s" % (start, inhalt, ende) if inhalt else "%s%s" % (start, ende)
    return re.sub(re.escape(start) + r".*?" + re.escape(ende), lambda _: neu, seite, flags=re.S)


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        sys.exit("Fehler: keine URL uebergeben.")
    url = sys.argv[1].strip()

    anfrage = urllib.request.Request(url, headers={"User-Agent": "ftv-hohenstaufen-website"})
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        roh = antwort.read().decode("utf-8", "replace")
    try:
        daten = json.loads(roh)
    except json.JSONDecodeError as fehler:
        sys.exit("Fehler: die URL liefert kein gueltiges JSON (%s)." % fehler)
    if not isinstance(daten, dict) or "scheduled_events" not in daten:
        sys.exit("Fehler: im JSON fehlt das Feld scheduled_events.")

    # Was die Schnittstelle mitschickt, steht so im Aktionsprotokoll. Damit
    # faellt auf, wenn Gaudeam ein neues Feld liefert, das hier noch niemand
    # auswertet -- etwa eine eigene Kennzeichnung fuer Online-Termine.
    roh_termine = [t for t in (daten.get("scheduled_events") or []) if isinstance(t, dict)]
    felder = sorted({schluessel for t in roh_termine for schluessel in t})
    if felder:
        print("Felder je Termin: %s" % ", ".join(felder))
        unbekannt = [f for f in felder if f not in ("name", "place", "date")]
        if unbekannt:
            print("Davon nicht ausgewertet: %s" % ", ".join(unbekannt))
    orte = sorted({(t.get("place") or "").strip() for t in roh_termine})
    if orte:
        print("Orte in den Rohdaten: %s" % " | ".join(repr(o) for o in orte))

    alle, uebersprungen = termine_lesen(daten)
    heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    kommend = sorted((e for e in alle if e["start"] >= heute), key=lambda e: e["start"])[:MAX_TERMINE]
    semester = (daten.get("semester") or "").strip()
    sonstige = daten.get("other_events") or []

    print("%d Termine gelesen, %d davon kommend." % (len(alle), len(kommend)))
    if semester:
        print("Semester: %s" % semester)
    if uebersprungen:
        print("Uebersprungen: %s" % ", ".join(uebersprungen))

    inhalt = {
        "semester": semester,
        "termine": [{"start": e["start"].strftime("%Y-%m-%dT%H:%M:%S"),
                     "ende": e["ende"].strftime("%Y-%m-%dT%H:%M:%S") if e["ende"] else None,
                     "titel": e["name"], "ort": e["ort"]} for e in kommend],
        "ohne_festen_termin": sonstige,
    }
    # Der Zeitstempel allein ist kein Grund, die Datei neu zu schreiben. Sonst
    # entstuende bei jedem Lauf ein Commit, obwohl sich nichts geaendert hat.
    alt = None
    if os.path.exists(JSON_DATEI):
        try:
            with open(JSON_DATEI, encoding="utf-8") as fh:
                alt = json.load(fh)
        except (OSError, json.JSONDecodeError):
            alt = None
    if alt is None or {k: v for k, v in alt.items() if k != "aktualisiert"} != inhalt:
        os.makedirs(os.path.dirname(JSON_DATEI), exist_ok=True)
        with open(JSON_DATEI, "w", encoding="utf-8") as fh:
            json.dump(dict(aktualisiert=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), **inhalt),
                      fh, ensure_ascii=False, indent=2)
        print("%s aktualisiert." % JSON_DATEI)
    else:
        print("%s unveraendert." % JSON_DATEI)

    # In den Kalender kommen alle Termine des Semesters, auch die vergangenen.
    # Wer abonniert hat, soll spaeter noch nachsehen koennen, wann was war.
    ics_schreiben(alle, semester)

    site_url = (os.environ.get("SITE_URL") or "").strip() or STANDARD_SITE_URL

    with open(HTML_DATEI, encoding="utf-8") as fh:
        seite = fh.read()
    neu = ersetzen(seite, "TERMINE", liste_bauen(kommend))
    neu = ersetzen(neu, "SEMESTER", "im " + escape(semester) if semester else "im Semester")
    neu = ersetzen(neu, "SONSTIGES", sonstiges_bauen(sonstige))
    neu = ersetzen(neu, "KALENDERLINKS", kalenderlinks_bauen(site_url))
    if neu == seite:
        print("Keine Aenderung noetig.")
        return
    with open(HTML_DATEI, "w", encoding="utf-8") as fh:
        fh.write(neu)
    print("%s aktualisiert." % HTML_DATEI)


if __name__ == "__main__":
    main()
