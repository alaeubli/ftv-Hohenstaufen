#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Holt den Vereinskalender als iCal und schreibt die Termine in die Website.

Aufruf:  python3 scripts/kalender.py <ICS-URL>

Erzeugt data/termine.json (Rohdaten) und ersetzt in veranstaltungen.html den
Bereich zwischen den Markern TERMINE:START und TERMINE:END durch fertiges HTML.
Damit steht die Terminliste direkt im Quelltext: sie ist ohne JavaScript
sichtbar und fuer Suchmaschinen lesbar.

Bewusst ohne Fremdbibliotheken, damit die Action nichts installieren muss.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
          "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
# Ganztaegige Termine bekommen keine Uhrzeit, alles andere schon.
MARK_START = "<!-- TERMINE:START -->"
MARK_END = "<!-- TERMINE:END -->"
HTML_DATEI = "veranstaltungen.html"
JSON_DATEI = "data/termine.json"
MAX_TERMINE = 12


def entfalten(text):
    """iCal bricht lange Zeilen um; Fortsetzungen beginnen mit Leerzeichen/Tab."""
    return re.sub(r"\r?\n[ \t]", "", text)


def wert(zeile):
    """'DTSTART;TZID=Europe/Berlin:20261018T200000' -> ('DTSTART', params, wert)"""
    name, _, rest = zeile.partition(":")
    schluessel, _, params = name.partition(";")
    return schluessel.upper(), params, rest


def text_feld(rohwert):
    """iCal-Escapes aufloesen (\\n, \\, \; \\,)."""
    return (rohwert.replace("\\n", " ").replace("\\N", " ")
            .replace("\\,", ",").replace("\;", ";").replace("\\\\", "\\").strip())


def zeit(rohwert, params):
    """Gibt (datetime, ganztaegig) zurueck. Zeiten werden als lokal behandelt,
    UTC-Angaben (Endung Z) werden auf Europe/Berlin umgerechnet."""
    roh = rohwert.strip()
    if "VALUE=DATE" in params.upper() or len(roh) == 8:
        return datetime.strptime(roh[:8], "%Y%m%d"), True
    if roh.endswith("Z"):
        d = datetime.strptime(roh[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        # Naeherung fuer Europe/Berlin ohne Zusatzbibliothek: Sommerzeit
        # von Ende Maerz bis Ende Oktober.
        versatz = 2 if 3 < d.month < 11 else 1
        return (d + timedelta(hours=versatz)).replace(tzinfo=None), False
    return datetime.strptime(roh[:15], "%Y%m%dT%H%M%S"), False


def termine_lesen(ics):
    """Liest VEVENT-Bloecke. Serientermine (RRULE) werden uebersprungen und
    gemeldet, damit niemand denkt, sie seien stillschweigend verschwunden."""
    eintraege, serien = [], 0
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", entfalten(ics), re.S):
        felder = {}
        for zeile in block.strip().splitlines():
            if ":" not in zeile:
                continue
            schluessel, params, roh = wert(zeile.strip())
            if schluessel in ("SUMMARY", "LOCATION", "DESCRIPTION", "RRULE"):
                felder[schluessel] = text_feld(roh)
            elif schluessel == "DTSTART":
                felder["START"], felder["GANZTAG"] = zeit(roh, params)
        if "START" not in felder or not felder.get("SUMMARY"):
            continue
        if felder.get("RRULE"):
            serien += 1
            continue
        eintraege.append(felder)
    return eintraege, serien


def html_bauen(eintraege):
    if not eintraege:
        return ('<p class="font-body-md text-body-md text-on-surface-variant text-center">'
                'Aktuell stehen keine Termine an. Schau bald wieder vorbei oder frag uns '
                'kurz per WhatsApp.</p>')
    teile = []
    for e in eintraege:
        d = e["START"]
        uhrzeit = "ganztägig" if e["GANZTAG"] else d.strftime("%H:%M Uhr")
        ort = escape(e.get("LOCATION", "") or "Hohenstaufenhaus")
        beschreibung = escape(e.get("DESCRIPTION", "") or "")
        teile.append('''<article class="flex gap-4 sm:gap-6 items-start sm:items-center bg-surface-container-lowest rounded-xl border border-surface-container p-4 sm:p-6 shadow-[0_10px_30px_rgba(32,89,48,0.03)] hover:shadow-[0_15px_40px_rgba(32,89,48,0.06)] hover:-translate-y-0.5 transition-all duration-300">
<div class="flex-shrink-0 flex flex-col items-center justify-center w-14 h-14 sm:w-20 sm:h-20 bg-secondary-container rounded-lg">
<span class="font-display-lg text-body-lg sm:text-headline-md font-semibold text-primary leading-none">{tag:02d}</span>
<span class="font-label-sm text-label-sm uppercase text-primary mt-1">{monat}</span>
</div>
<div class="flex-1 min-w-0">
<h3 class="font-headline-md text-body-lg sm:text-headline-md text-on-surface mb-stack-sm">{titel}</h3>
<div class="flex flex-wrap items-center gap-x-4 sm:gap-x-6 gap-y-1 font-body-md text-body-md text-on-surface-variant{mb}">
<span class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-lg">schedule</span>{uhrzeit}</span>
<span class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-lg">location_on</span>{ort}</span>
</div>{text}
</div>
</article>'''.format(
            tag=d.day, monat=MONATE[d.month - 1], titel=escape(e["SUMMARY"]),
            uhrzeit=uhrzeit, ort=ort,
            mb=" mb-stack-sm" if beschreibung else "",
            text=('\n<p class="font-body-md text-body-md text-on-surface-variant/80">%s</p>'
                  % beschreibung) if beschreibung else ""))
    return "\n".join(teile)


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        sys.exit("Fehler: keine ICS-URL uebergeben. Ist das Secret KALENDER_ICS_URL gesetzt?")
    url = sys.argv[1].strip()
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]

    with urllib.request.urlopen(url, timeout=60) as antwort:
        ics = antwort.read().decode("utf-8", "replace")
    if "BEGIN:VCALENDAR" not in ics:
        sys.exit("Fehler: die URL liefert keine iCal-Datei.")

    alle, serien = termine_lesen(ics)
    heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    kommend = sorted((e for e in alle if e["START"] >= heute), key=lambda e: e["START"])
    kommend = kommend[:MAX_TERMINE]
    print("%d Termine gelesen, %d davon kommend, %d Serientermine uebersprungen."
          % (len(alle), len(kommend), serien))

    os.makedirs(os.path.dirname(JSON_DATEI), exist_ok=True)
    with open(JSON_DATEI, "w", encoding="utf-8") as fh:
        json.dump({
            "aktualisiert": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "termine": [{
                "start": e["START"].strftime("%Y-%m-%dT%H:%M:%S"),
                "ganztaegig": e["GANZTAG"],
                "titel": e["SUMMARY"],
                "ort": e.get("LOCATION", ""),
                "beschreibung": e.get("DESCRIPTION", ""),
            } for e in kommend],
        }, fh, ensure_ascii=False, indent=2)

    with open(HTML_DATEI, encoding="utf-8") as fh:
        seite = fh.read()
    if MARK_START not in seite or MARK_END not in seite:
        sys.exit("Fehler: Marker %s / %s fehlen in %s." % (MARK_START, MARK_END, HTML_DATEI))
    neu = "%s\n%s\n%s" % (MARK_START, html_bauen(kommend), MARK_END)
    ersetzt = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
                     lambda _: neu, seite, flags=re.S)
    if ersetzt == seite:
        print("Keine Aenderung noetig.")
        return
    with open(HTML_DATEI, "w", encoding="utf-8") as fh:
        fh.write(ersetzt)
    print("%s aktualisiert." % HTML_DATEI)


if __name__ == "__main__":
    main()
