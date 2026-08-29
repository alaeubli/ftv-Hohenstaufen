# Website der FtV Hohenstaufen zu Aalen

Statische Website ohne Build-Schritt. Die HTML-Dateien liegen fertig im
Repository und werden direkt von GitHub Pages ausgeliefert.

| Datei                  | Seite                  |
|------------------------|------------------------|
| `index.html`           | Startseite             |
| `haus.html`            | Das Hohenstaufenhaus   |
| `zimmer.html`          | Zimmer mieten          |
| `veranstaltungen.html` | Veranstaltungen        |
| `404.html`             | Fehlerseite            |

`.nojekyll` sorgt dafür, dass Pages die Dateien unverändert ausliefert.

## Veröffentlichen

1. Branch nach `main` mergen.
2. **Settings → Pages** → Source *Deploy from a branch*, Branch `main`, Ordner `/ (root)`.
3. Bei eigener Domain zusätzlich eine Datei `CNAME` mit dem Domainnamen anlegen.

## Termine automatisch aktualisieren

Die Terminliste auf `veranstaltungen.html` wird von einer GitHub Action aus dem
Vereinskalender befüllt. Auf der Seite muss niemand etwas pflegen: Termin im
Kalender anlegen, fertig.

**Einrichten:**

1. Im Kalender die private iCal-Adresse kopieren.
   Google Kalender: *Einstellungen → Kalender auswählen → Privateadresse im
   iCal-Format*. Die Adresse endet auf `.ics`.
2. Im Repository unter **Settings → Secrets and variables → Actions → New
   repository secret** ein Secret mit dem Namen `KALENDER_ICS_URL` anlegen und
   die Adresse einfügen.
3. Unter **Actions → Termine aus dem Kalender aktualisieren → Run workflow**
   einmal von Hand starten.

Danach läuft die Action täglich um 04:15 UTC. Sie schreibt:

* `veranstaltungen.html` – die fertige Terminliste zwischen den Markern
  `<!-- TERMINE:START -->` und `<!-- TERMINE:END -->`
* `data/termine.json` – dieselben Termine als Rohdaten

Geändert wird nur, wenn sich wirklich etwas geändert hat. Es entsteht also
nicht jeden Tag ein Commit.

**Gut zu wissen:**

* Angezeigt werden die nächsten zwölf kommenden Termine. Vergangene fallen
  automatisch raus.
* Ganztägige Termine bekommen statt einer Uhrzeit den Hinweis „ganztägig“.
* Serientermine (wöchentlicher Stammtisch und Ähnliches) werden übersprungen
  und im Aktionsprotokoll gezählt. Wer sie auf der Seite haben will, legt sie
  im Kalender als Einzeltermine an.
* Titel, Ort und Beschreibung aus dem Kalender landen unverändert auf der
  Seite, werden aber HTML-escaped. Ein Kalendereintrag kann also keinen Code
  einschleusen.
* Solange das Secret fehlt, bricht die Action mit einer klaren Meldung ab und
  die Beispieltermine auf der Seite bleiben stehen.

Manuell testen lässt sich das Skript mit einer beliebigen ICS-Adresse:

```
python3 scripts/kalender.py "https://.../basic.ics"
```

## Noch offen

* Echte Fotos statt der Platzhalter von `picsum.photos` (im Quelltext mit
  `TODO` markiert)
* WhatsApp-Nummer: überall steht der Platzhalter `49XXXXXXXXXX`. Einmal in
  allen Dateien ersetzen, dann sind alle WhatsApp-Buttons aktiv.
* Telefonnummer und E-Mail-Adresse gegenprüfen
* Mietpreise und die tatsächlichen Zimmergrößen eintragen
* Impressum, Datenschutz und Newsletter verlinken (stehen im Footer auf `#`)
