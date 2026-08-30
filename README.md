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
| `impressum.html`       | Impressum              |
| `datenschutz.html`     | Datenschutz            |

`.nojekyll` sorgt dafür, dass Pages die Dateien unverändert ausliefert.

## Veröffentlichen

1. Branch nach `main` mergen.
2. **Settings → Pages** → Source *Deploy from a branch*, Branch `main`, Ordner `/ (root)`.
3. Bei eigener Domain zusätzlich eine Datei `CNAME` mit dem Domainnamen anlegen.

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
* **Google Fonts wird von Google-Servern geladen.** Dabei geht die IP-Adresse
  der Besucher an Google. Das LG Muenchen I hat das 2022 als Verstoss gegen die
  DSGVO gewertet (Az. 3 O 17493/20). Sauberer waere, die Schriften selbst
  auszuliefern. Gleiches gilt fuer die Tailwind-Bibliothek.
