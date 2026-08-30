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
