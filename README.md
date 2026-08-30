# Website der FtV Hohenstaufen zu Aalen

Statische Website. Die HTML-Dateien liegen fertig im Repository und werden
direkt von GitHub Pages ausgeliefert. Schriften, Symbole, Bilder und CSS liegen
unter `assets/`, es wird nichts von fremden Servern nachgeladen.

| Datei                  | Seite                  |
|------------------------|------------------------|
| `index.html`           | Startseite             |
| `haus.html`            | Das Hohenstaufenhaus   |
| `zimmer.html`          | Zimmer mieten          |
| `veranstaltungen.html` | Veranstaltungen        |
| `404.html`             | Fehlerseite            |
| `impressum.html`       | Impressum              |
| `datenschutz.html`     | Datenschutz            |
| `assets/`              | CSS, Schriften, Platzhalterbild |

`.nojekyll` sorgt dafür, dass Pages die Dateien unverändert ausliefert.

## Veröffentlichen

1. Branch nach `main` mergen.
2. **Settings → Pages** → Source *Deploy from a branch*, Branch `main`, Ordner `/ (root)`.
3. Bei eigener Domain zusätzlich eine Datei `CNAME` mit dem Domainnamen anlegen.

## CSS neu erzeugen

Die Gestaltung steckt in `assets/styles.css`. Die Datei wird aus
`assets/src.css` und den Klassen in den HTML-Dateien erzeugt. **Wer im HTML
neue Tailwind-Klassen einbaut, muss sie danach neu erzeugen**, sonst fehlt die
passende Regel und das Element sieht kaputt aus:

```
bash scripts/build-css.sh
```

Das Skript installiert beim ersten Lauf die noetigen Pakete. Reine Textaenderungen
brauchen keinen Durchlauf.

Die Symbole sind als SVG direkt im HTML eingebettet, es wird also keine
Icon-Schrift geladen. Die Pfaddaten stammen aus Material Symbols (Apache 2.0),
die Schriften Montserrat und Inter von Fontsource (SIL Open Font License).

## Fotos einsetzen

Die Fotos liegen in `assets/bilder/`. Neue Fotos so aufbereiten:

```
pip install pillow
python3 scripts/bilder-vorbereiten.py haus-aussen.jpg garten.jpg kneipsaal.jpg
```

Das Skript verkleinert auf hoechstens 1920 Pixel Breite, speichert als JPEG und
**entfernt saemtliche EXIF-Daten**. Kameras und Handys schreiben dort oft
GPS-Koordinaten hinein, die sonst mit dem Bild oeffentlich waeren. Ergebnis
landet in `assets/bilder/`. Danach im HTML den Dateinamen eintragen.

Von den sieben vermieteten Zimmern gibt es noch keine Fotos, die Karten auf der
Zimmerseite zeigen deshalb nur Etage und Groesse.

Hintergrundbilder werden im Stylesheet unscharf gezeichnet, damit man nur
Silhouetten sieht und der Text darauf lesbar bleibt:

* Hero: `blur-lg md:blur-xl` zusammen mit `scale-110`
* Bildkarten mit Text darauf: `blur-md` mit `scale-105`
* Bilder ohne Text darauf und die Zimmerfotos bleiben scharf

Das `scale` ist noetig, weil die Unschaerfe sonst an den Bildraendern ausfranst.
Staerker oder schwaecher: die Klasse im HTML aendern und `bash scripts/build-css.sh`
laufen lassen.

## Termine automatisch aktualisieren

Die Terminliste auf `veranstaltungen.html` wird von einer GitHub Action aus der
Vereins-Schnittstelle befuellt:

```
https://hohenstaufen-aalen.gaudeam.de/api/v1/open_events.json
```

Auf der Website muss niemand etwas pflegen. Termin in Gaudeam anlegen, fertig.

Die Action laeuft montags um 04:15 UTC, nach jeder Aenderung am Skript und auf
Knopfdruck unter **Actions → Termine aktualisieren → Run workflow**. Ein Secret
braucht es nicht, die Schnittstelle ist oeffentlich. Sollte sich die Adresse
einmal aendern, legt man unter **Settings → Secrets and variables → Actions →
Variables** eine Variable `TERMINE_URL` an; die sticht die Voreinstellung.

Zwei Eigenheiten von GitHub, die man kennen sollte:

* Geplante Laeufe starten **nur auf dem Standardbranch**. Solange dieser Stand
  auf einem Feature-Branch liegt, passiert nach Zeitplan nichts. Nach dem Merge
  nach `main` laeuft es von selbst.
* Liegt im Repository 60 Tage lang keine Aktivitaet, schaltet GitHub geplante
  Workflows ab und meldet das per Mail. Ein Klick auf *Enable workflow*
  reaktiviert sie.

Geschrieben werden:

* `veranstaltungen.html` zwischen den Markern `TERMINE`, `SEMESTER` und
  `SONSTIGES`
* `data/termine.json` mit denselben Terminen als Rohdaten

Committet wird nur, wenn sich wirklich etwas geaendert hat. Der Zeitstempel in
`data/termine.json` zaehlt dabei nicht als Aenderung, sonst entstuende bei jedem
Lauf ein Commit.

**Gut zu wissen:**

* Angezeigt werden die naechsten zwoelf Termine, vergangene fallen automatisch
  raus. Steht nichts an, erscheint ein freundlicher Hinweis statt einer leeren
  Liste.
* Das Feld `semester` landet in der Ueberschrift, aus „Termine im Semester“
  wird also „Termine im WS 26/27“.
* Eintraege aus `other_events` (Formate ohne festen Termin, etwa Fuchsenabende)
  stehen als Hinweis unter der Liste.
* Orte werden fuer Gaeste ausgeschrieben: `adH` wird zu „auf dem Hause“, die
  eigene Adresse zu „Hohenstaufenhaus, Mozartstr. 31“. Die Zuordnung steht im
  Skript unter `ORTE`.
* Die Zeitangaben kommen im Format `MM/TT/JJJJ`. Steht an erster Stelle eine
  Zahl groesser zwoelf, liest das Skript stattdessen `TT/MM/JJJJ`. Ein Wechsel
  des Formats verschiebt die Termine also nicht stillschweigend um Monate.
* Termine ohne Namen oder mit unlesbarem Datum werden uebersprungen und im
  Aktionsprotokoll namentlich genannt.
* Titel und Ort werden HTML-escaped. Ein Eintrag aus der Schnittstelle kann
  keinen Code auf die Seite bringen.

Manuell testen:

```
python3 scripts/kalender.py "https://hohenstaufen-aalen.gaudeam.de/api/v1/open_events.json"
```

## Noch offen

* Echte Fotos statt der Platzhalter von `picsum.photos` (im Quelltext mit
  `TODO` markiert)
* WhatsApp-Nummer: überall steht der Platzhalter `49XXXXXXXXXX`. Einmal in
  allen Dateien ersetzen, dann sind alle WhatsApp-Buttons aktiv.
* Telefonnummer und E-Mail-Adresse gegenprüfen
* Mietpreise und die tatsächlichen Zimmergrößen eintragen
* **Impressum und Datenschutz sind Entwuerfe.** Die rot markierten Stellen
  ergaenzen (Vorstand, Vereinsregister, verantwortliche Person) und beides vor
  dem Livegang juristisch pruefen lassen.

