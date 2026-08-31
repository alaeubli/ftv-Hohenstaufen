#!/usr/bin/env bash
# Erzeugt assets/styles.css aus assets/src.css und den Klassen in den HTML-Dateien.
# Immer ausfuehren, wenn im HTML neue Tailwind-Klassen dazukommen.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d node_modules ]; then
  echo "Installiere Abhaengigkeiten ..."
  npm install --no-audit --no-fund
fi
node_modules/.bin/tailwindcss -c tailwind.config.js -i assets/src.css -o assets/styles.css --minify
echo "assets/styles.css neu erzeugt."

# Kurzes Kuerzel aus dem Inhalt der CSS-Datei an den Link im HTML haengen.
# Ohne das liefert der Browser nach einer Aenderung unter Umstaenden noch die
# alte CSS-Datei aus dem Cache aus. Neue Klassen fehlen dann einfach, ohne dass
# es eine Fehlermeldung gibt: Die Seite sieht dann falsch aus, aber nicht kaputt.
HASH=$(sha256sum assets/styles.css | cut -c1-8)
for f in *.html; do
  sed -i -E "s|href=\"assets/styles\.css(\?v=[0-9a-f]+)?\"|href=\"assets/styles.css?v=${HASH}\"|g" "$f"
done
echo "Cache-Kuerzel ?v=${HASH} in allen HTML-Dateien gesetzt."
