#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Holt die Termine aus der Vereins-API und schreibt sie in die Website.

Aufruf:  python3 scripts/kalender.py <URL zur open_events.json>

Erwartetes Format:
    {"semester": "WS 26/27",
     "scheduled_events": [{"name": ..., "place": ..., "date": [start, ende]}, ...],
     "other_events": ["Fuchsenabende", ...]}

Zeitangaben kommen als "MM/DD/YYYY HH:MM:SS" in Ortszeit.

Geschrieben werden data/termine.json (Rohdaten) und drei Bereiche in
veranstaltungen.html, jeweils zwischen Markern. Dadurch steht die Liste
direkt im Quelltext: ohne JavaScript sichtbar und fuer Suchmaschinen lesbar.

Bewusst ohne Fremdbibliotheken, damit die Action nichts installieren muss.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from html import escape

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
          "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
HTML_DATEI = "veranstaltungen.html"
JSON_DATEI = "data/termine.json"
MAX_TERMINE = 12

# Die API liefert Orte knapp und im Verbindungsjargon. Fuer Gaeste ausschreiben.
EIGENE_ADRESSE = "Mozartstr. 31, 73430 Aalen, Deutschland"
ORTE = {
    EIGENE_ADRESSE: "Hohenstaufenhaus, Mozartstr. 31",
    "adH": "auf dem Hause",
}


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


def ort_lesbar(roh):
    roh = (roh or "").strip()
    if not roh:
        return "Hohenstaufenhaus"
    if roh in ORTE:
        return ORTE[roh]
    return re.sub(r",\s*Deutschland\s*$", "", roh)


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
                          "ort": ort_lesbar(roh.get("place"))})
    return eintraege, uebersprungen


def liste_bauen(eintraege):
    if not eintraege:
        return ('<p class="font-body-md text-body-md text-on-surface-variant text-center">'
                'Gerade steht nichts an. Schau bald wieder vorbei oder frag uns kurz '
                'per WhatsApp, was als Nächstes läuft.</p>')
    teile = []
    for e in eintraege:
        d = e["start"]
        teile.append('''<article class="flex gap-4 sm:gap-6 items-start sm:items-center bg-surface-container-lowest rounded-xl border border-surface-container p-4 sm:p-6 shadow-[0_10px_30px_rgba(32,89,48,0.03)] hover:shadow-[0_15px_40px_rgba(32,89,48,0.06)] hover:-translate-y-0.5 transition-all duration-300">
<div class="flex-shrink-0 flex flex-col items-center justify-center w-14 h-14 sm:w-20 sm:h-20 bg-secondary-container rounded-lg">
<span class="font-display-lg text-body-lg sm:text-headline-md font-semibold text-primary leading-none">{tag:02d}</span>
<span class="font-label-sm text-label-sm uppercase text-primary mt-1">{monat}</span>
</div>
<div class="flex-1 min-w-0">
<h3 class="font-headline-md text-body-lg sm:text-headline-md text-on-surface mb-stack-sm break-words hyphens-auto">{titel}</h3>
<div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-1 sm:gap-x-6 font-body-md text-body-md text-on-surface-variant">
<span class="flex items-center gap-2 min-w-0"><span class="material-symbols-outlined text-primary text-lg flex-shrink-0">schedule</span>{uhrzeit}</span>
<span class="flex items-center gap-2 min-w-0"><span class="material-symbols-outlined text-primary text-lg flex-shrink-0">location_on</span><span class="min-w-0 break-words">{ort}</span></span>
</div>
</div>
</article>'''.format(tag=d.day, monat=MONATE[d.month - 1],
                     titel=escape(e["name"]),
                     uhrzeit=escape(uhrzeit_text(d, e["ende"])),
                     ort=escape(e["ort"])))
    return "\n".join(teile)


def sonstiges_bauen(namen):
    namen = [n.strip() for n in (namen or []) if n and n.strip()]
    if not namen:
        return ""
    aufzaehlung = escape(namen[0]) if len(namen) == 1 else \
        "%s und %s" % (", ".join(escape(n) for n in namen[:-1]), escape(namen[-1]))
    return ('<div class="mt-stack-lg bg-surface-container-low rounded-xl p-6 flex flex-col '
            'sm:flex-row sm:items-center gap-4">\n'
            '<span class="material-symbols-outlined text-primary flex-shrink-0">more_horiz</span>\n'
            '<p class="font-body-md text-body-md text-on-surface-variant">Dazu kommen über das '
            'Semester verteilt %s. Die Termine dafür stehen noch nicht fest, frag uns einfach '
            'kurz per WhatsApp.</p>\n</div>' % aufzaehlung)


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

    with open(HTML_DATEI, encoding="utf-8") as fh:
        seite = fh.read()
    neu = ersetzen(seite, "TERMINE", liste_bauen(kommend))
    neu = ersetzen(neu, "SEMESTER", "im " + escape(semester) if semester else "im Semester")
    neu = ersetzen(neu, "SONSTIGES", sonstiges_bauen(sonstige))
    if neu == seite:
        print("Keine Aenderung noetig.")
        return
    with open(HTML_DATEI, "w", encoding="utf-8") as fh:
        fh.write(neu)
    print("%s aktualisiert." % HTML_DATEI)


if __name__ == "__main__":
    main()
