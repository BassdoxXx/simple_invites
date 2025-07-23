# Simple Invites 🧾

**Simple Invites** ist ein minimalistisches Einladungs- und Rückmeldetool für Veranstaltungen – ideal z. B. für Feuerwehren, Vereine oder private Feiern.

## ✨ Features

- Web-Interface für Einladungserstellung
- QR-Code-Generierung für jede Einladung
- Gäste können Zu-/Absagen inklusive Personenanzahl & Getränkewünsche angeben
- Antwort jederzeit änderbar (bis 2 Tage vor Event)
- Admin-Bereich mit Passwortschutz & Passwort-Änderung
- Optional: WhatsApp-Benachrichtigung (via CallMeBot)
- Vollständig in Docker oder lokal nutzbar
- Übersichtliche Statistiken im Admin-Bereich (z. B. Anzahl der Zusagen)
- **Automatische Tischnummernvergabe**:
  - Die nächste freie Tischnummer wird automatisch vergeben.
  - Manuelle Eingabe ist möglich, aber doppelte Tischnummern werden verhindert.
- **Eindeutige Gastnamen**:
  - Es wird sichergestellt, dass kein Name doppelt vorkommt.

## 🚀 Nutzung

1. **Clonen**:

```bash
git clone https://github.com/BassdoxXx/simple_invites.git
cd simple_invites
```

2. **Installieren** (lokal):

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

3. **Zugreifen**:

Öffne [http://localhost:5000](http://localhost:5000) im Browser.

- Login: `admin`
- Passwort: `changeme` (beim ersten Login wird Änderung erzwungen)

4. **Docker (optional)**:

```bash
docker build -t simple_invites .
docker run -p 5000:5000 simple_invites
```

## ⚙️ Ordnerstruktur

```
simple_invites/
│
├── app/
│   ├── __init__.py          # Flask-App-Setup
│   ├── main.py              # Einstiegspunkt der Anwendung
│   ├── models.py            # SQLAlchemy-Modelle
│   ├── blueprints/          # Flask-Blueprints (auth, admin, public)
│   ├── utils/               # Hilfsfunktionen (QR-Code, Passwort-Logik)
│   ├── templates/           # HTML-Templates (Tailwind)
│   └── static/              # Statische Dateien (CSS, QR-Codes)
│
├── data/simple_invites.db   # SQLite-Datenbank (wird beim ersten Start erstellt)
├── requirements.txt         # Python-Abhängigkeiten
└── Dockerfile               # Docker-Setup
```

## 🛠️ Konfiguration

- **WhatsApp-Benachrichtigungen**:
  - Telefonnummer und API-Key in den Admin-Einstellungen hinterlegen.
  - CallMeBot wird verwendet, um Nachrichten zu versenden.

- **Passwortschutz**:
  - Beim ersten Login wird eine Passwortänderung erzwungen.
  - Passwörter werden sicher gehasht gespeichert.

## 📖 Hinweise

- **QR-Codes**:
  - QR-Codes werden im Ordner `static/qrcodes/` gespeichert.
  - Beim Löschen einer Einladung wird der zugehörige QR-Code automatisch entfernt.

- **Datenbank**:
  - Die SQLite-Datenbank wird automatisch im Ordner `data/` erstellt.
  - Für produktive Umgebungen kann eine andere Datenbank (z. B. PostgreSQL) konfiguriert werden.

---

Mit ❤️ und CoPilot gebaut für das 150-jährige Jubiläum der Freiwilligen Feuerwehr Windischletten – oder jedes andere Event.