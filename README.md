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

## 🚀 Nutzung

1. **Clonen**:

```bash
git clone https://github.com/dein-benutzername/simple_invites.git
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
- Passwort: `admin123` (beim ersten Login wird Änderung erzwungen)

## ⚙️ Ordnerstruktur

```
simple_invites/
│
├── app/
│   ├── main.py              # Flask-Anwendung
│   ├── models.py            # SQLAlchemy-Modelle
│   ├── qr_utils.py          # QR-Code-Erzeugung
│   └── templates/           # HTML-Templates (Tailwind)
│
├── static/qrcodes/          # QR-Code Bilder
└── data/simple_invites.db   # SQLite-Datenbank (beim ersten Start erstellt)
```

---

Mit ❤️ gebaut für das 150-jährige Jubiläum der Freiwilligen Feuerwehr Windischletten – oder jedes andere Event.
