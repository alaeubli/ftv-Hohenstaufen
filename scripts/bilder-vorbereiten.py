#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bereitet Fotos fuer die Website auf.

Aufruf:
    python3 scripts/bilder-vorbereiten.py haus-aussen.jpg garten.jpg
    python3 scripts/bilder-vorbereiten.py https://.../foto.jpg

Was passiert:
  * Bild wird auf hoechstens 1920 Pixel Breite verkleinert
  * als JPEG mit Qualitaet 82 gespeichert, das reicht fuer Bildschirme
  * saemtliche EXIF-Daten werden entfernt. Kameras schreiben dort oft
    GPS-Koordinaten und Geraetenamen hinein, die sonst oeffentlich waeren
  * Ergebnis landet in assets/bilder/

Danach den Dateinamen im HTML eintragen, dort wo jetzt
assets/platzhalter.svg steht. Die Unschaerfe fuer Hintergruende macht das
Stylesheet, die Bilder selbst bleiben scharf.

Benoetigt Pillow:  pip install pillow
"""
import os
import sys
import urllib.request

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow fehlt. Installieren mit: pip install pillow")

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "bilder")
MAX_BREITE = 1920
QUALITAET = 82


def laden(quelle):
    if quelle.startswith(("http://", "https://")):
        name = os.path.basename(quelle.split("?")[0]) or "bild.jpg"
        anfrage = urllib.request.Request(quelle, headers={"User-Agent": "ftv-hohenstaufen-website"})
        with urllib.request.urlopen(anfrage, timeout=60) as antwort:
            daten = antwort.read()
        import io as _io
        return name, Image.open(_io.BytesIO(daten))
    return os.path.basename(quelle), Image.open(quelle)


def aufbereiten(quelle):
    name, bild = laden(quelle)
    basis = os.path.splitext(name)[0].lower()
    for zeichen in " äöüß":
        basis = basis.replace(zeichen, {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", " ": "-"}[zeichen])

    # Drehung aus den EXIF-Daten anwenden, bevor diese verworfen werden
    try:
        from PIL import ImageOps
        bild = ImageOps.exif_transpose(bild)
    except Exception:
        pass
    bild = bild.convert("RGB")

    if bild.width > MAX_BREITE:
        hoehe = round(bild.height * MAX_BREITE / bild.width)
        bild = bild.resize((MAX_BREITE, hoehe), Image.LANCZOS)

    # Neues Bild ohne jegliche Metadaten aufbauen
    sauber = Image.new("RGB", bild.size)
    sauber.paste(bild)

    os.makedirs(ZIEL, exist_ok=True)
    ziel = os.path.join(ZIEL, basis + ".jpg")
    sauber.save(ziel, "JPEG", quality=QUALITAET, optimize=True, progressive=True)
    groesse = os.path.getsize(ziel) / 1024
    print("  %-34s %4d x %-4d  %6.0f KB   ->  assets/bilder/%s.jpg"
          % (name, sauber.width, sauber.height, groesse, basis))
    return basis


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print("Aufbereitet:")
    namen = [aufbereiten(q) for q in sys.argv[1:]]
    print("\nIm HTML eintragen, zum Beispiel:")
    print('  src="assets/bilder/%s.jpg"' % namen[0])


if __name__ == "__main__":
    main()
