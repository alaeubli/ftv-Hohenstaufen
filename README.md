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

## Das Wappen

`assets/bilder/wappen.png` ist freigestellt, hat also einen Alphakanal. **Nicht
durch `scripts/bilder-vorbereiten.py` schicken**: das Skript speichert als JPEG
und wuerde die Transparenz zerstoeren, das Wappen bekaeme einen schwarzen
Kasten. Es steht an drei Stellen:

* im Traditionsabschnitt der Startseite ueber der Ueberschrift
* in der Fusszeile jeder Seite, in einem hellen Kreis. Der Kreis ist noetig,
  weil die schwarze Helmdecke auf dem dunkelgruenen Grund sonst untergeht.
* als Favicon und Apple-Touch-Icon

Fuers Favicon (`assets/favicon-32.png`) ist **nur der Schild** ausgeschnitten,
ohne Helm und Helmdecke. Das ganze Wappen wird bei 32 Pixeln zu einem Farbfleck,
der Schild bleibt mit seinen vier Feldern erkennbar. Das Apple-Touch-Icon
(180 Pixel) zeigt dagegen das ganze Wappen, dort ist Platz genug; es hat einen
hellen Grund, weil iOS Transparenz sonst mit Schwarz unterlegt.

Die Vorlage ist nur 146 x 165 Pixel gross. Deshalb wird sie nirgends groesser
als 112 Pixel angezeigt, hochskaliert wuerde sie auf feinen Displays weich.
**Wer eine groessere Fassung oder ein SVG auftreibt, kann sie ersetzen** und die
Anzeigegroesse im Traditionsabschnitt anheben.

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

Die Action laeuft taeglich um 04:15 UTC, nach jeder Aenderung am Skript und auf
Knopfdruck unter **Actions → Termine aktualisieren → Run workflow**. Taeglich
deshalb, weil `termine.ics` abonniert wird: was hier nicht ankommt, sieht auch
in keinem fremden Kalender jemand. Aendert sich nichts, entsteht kein Commit. Ein Secret
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

* `veranstaltungen.html` zwischen den Markern `TERMINE`, `SEMESTER`,
  `SONSTIGES` und `KALENDERLINKS`
* `data/termine.json` mit denselben Terminen als Rohdaten
* `termine.ics`, der abonnierbare Kalender

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
* Beim Ort kennt das Skript genau drei Faelle. Alle Schreibweisen des eigenen
  Hauses (`adH`, „auf dem Hause“, „Hohenstaufenhaus“, die eigene Anschrift in
  jeder Variante) werden zu „auf dem Haus“ – damit derselbe Ort nicht einmal so
  und einmal als Adresse dasteht. Ein fremder Ort wird uebernommen, wie er
  kommt, nur ohne das angehaengte „, Deutschland“. Ein leeres Feld bleibt leer:
  dann steht bei dem Termin gar kein Ort. Die Erkennung steht im Skript unter
  `EIGENES_HAUS` und `EIGENE_STRASSE`, ein neuer Sonderfall gehoert dort hin.
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

## Der Kalender zum Abonnieren

`termine.ics` entsteht im selben Lauf aus denselben Daten. Es gibt also keinen
zweiten Ort, an dem jemand Termine pflegen muesste, und die Datei kann nicht
von der Liste auf der Seite abweichen.

Auf `veranstaltungen.html` stehen drei Wege hinein, alle auf dieselbe Datei:

* **Kalender abonnieren** benutzt `webcal:` mit der vollstaendigen
  https-Adresse dahinter, also **ein Doppelpunkt und keine zwei
  Schraegstriche**: `webcal:https://.../termine.ics`. Das ist eine gueltige
  opake URI, Browser lassen sie unveraendert, und eine App, die nur `webcal:`
  abschneidet, behaelt genau die richtige https-Adresse uebrig.
* **iCal-Datei laden** ist eine Momentaufnahme zum einmaligen Einlesen. Wer sie
  importiert, bekommt spaetere Verschiebungen **nicht** mit.
* Die Adresse im Klartext zum Selbstkopieren. Das ist der Weg fuer den Google
  Kalender (**Weitere Kalender → Per URL**) und fuer jede App, die von sich aus
  nicht nach einem Abo fragt. Nur so entsteht sicher ein Abo und kein Import. Google holt fremde Kalender
  allerdings nur ein- bis zweimal am Tag ab, kurzfristige Aenderungen kommen
  dort also spaeter an als bei Apple oder Outlook.

Zwei naheliegende Schreibweisen funktionieren **nicht**, beide wurden probiert:

* `webcal://https://...` mit zwei Schraegstrichen. Nach `//` erwartet jeder
  URL-Parser einen Hostnamen und liest dort `https` als Rechnernamen; Chromium
  formt das zu `webcal://https//alaeubli.github.io/...` um.
* `webcal://host/pfad`, die nach Norm richtige Form. Genau daran scheitern die
  Apps, die beim Import nur `webcal:` abschneiden: uebrig bleibt `//host/pfad`
  ohne Schema.

Der Preis der jetzigen Form: eine App, die das Schema stur durch `https:`
ersetzt, bekommt `https:https://...`. Fuer die steht die Adresse im Klartext
darunter, das ist der Weg, der ueberall geht.

Die Adresse muss absolut sein, weil Kalender-Apps sie von aussen abrufen. Sie
kommt aus der Umgebungsvariablen `SITE_URL`; voreingestellt ist die
GitHub-Pages-Adresse. **Kommt eine eigene Domain dazu, unter Settings → Secrets
and variables → Actions → Variables eine Variable `SITE_URL` anlegen**, sonst
zeigen die Abo-Links weiter auf die alte Adresse.

Weitere Eigenheiten:

* Im Kalender stehen **alle** Termine des Semesters, auch vergangene. Auf der
  Seite stehen nur die naechsten zwoelf.
* Als Ort steht dort die vollstaendige Anschrift statt „auf dem Haus“, damit
  die Navigation im Handy etwas damit anfangen kann. Ein Termin ohne Ort
  bekommt gar kein `LOCATION`-Feld.
* Termine ohne Ende bekommen zwei Stunden Dauer, sonst zeigen viele Apps einen
  Eintrag von null Minuten.
* Die Kennung eines Termins wird aus Titel und Startzeit abgeleitet und bleibt
  damit ueber alle Laeufe gleich. Verschiebt sich ein Termin um die Uhrzeit,
  gilt er als neuer Eintrag und der alte verschwindet aus dem Abo.
* Zeiten tragen die Zone `Europe/Berlin`, ein Abo aus dem Ausland verrutscht
  also nicht.
* Wie bei `data/termine.json` zaehlt der Zeitstempel nicht als Aenderung.

Bis eine Verschiebung im fremden Kalender ankommt, vergehen zwei Wartezeiten:
erst laeuft die Action (taeglich), dann sieht die Kalender-App der Person nach.
Wie oft sie das tut, entscheidet sie selbst; `REFRESH-INTERVAL` in der Datei ist
nur eine Bitte um alle zwoelf Stunden, an die sich Apple und Thunderbird halten
und Google nicht. Wirklich kurzfristige Absagen gehoeren deshalb weiter in die
Gruppe, nicht allein in den Kalender.

## Noch offen

* WhatsApp-Nummer: überall steht der Platzhalter `49XXXXXXXXXX`. Einmal in
  allen Dateien ersetzen, dann sind alle WhatsApp-Buttons aktiv.
* Telefonnummer und E-Mail-Adresse gegenprüfen
* Mietpreise stehen bewusst nicht auf der Seite, sie werden auf Anfrage
  genannt. Die Zimmerseite sagt nur, dass die Miete All-in ist.
* **Impressum und Datenschutz sind Entwuerfe.** Die rot markierten Stellen
  ergaenzen (Vorstand, Vereinsregister, verantwortliche Person) und beides vor
  dem Livegang juristisch pruefen lassen.

