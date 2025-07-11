# Simple Invites 🧾

![Docker Build & Push](https://github.com/BassdoxXx/simple_invites/actions/workflows/docker.yml/badge.svg)

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

### 1. Clonen

```bash
git clone https://github.com/BassdoxXx/simple_invites.git
cd simple_invites
```

### 2. Lokale Installation

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

### 3. Zugriff

Öffne [http://localhost:5000](http://localhost:5000) im Browser.

- Login: `admin`
- Passwort: `changeme` (beim ersten Login wird Änderung erzwungen)

### 4. Docker (empfohlen für Produktion)

#### Docker Compose

Erstelle eine Datei `docker-compose.yml` mit folgendem Inhalt:

```yaml
services:
  simple_invites:
    image: bassdoxxx/simple_invites:latest
    container_name: simple_invites
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./app/static:/app/app/static
      - ./data/simple_invites:/data/simple_invites
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=dein_geheimer_schluessel
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    networks:
      - core_net
```

Starte die Anwendung mit:

```bash
docker compose up -d
```

Die Datenbank und alle persistenten Daten werden im Ordner `./data/simple_invites` auf deinem Dockerhost gespeichert.

#### Automatischer Build & Push (optional)

Das Image kann automatisch per GitHub Actions gebaut und zu Docker Hub gepusht werden.  
Lege dazu die Zugangsdaten als Secrets im Repository an (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`).

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
├── data/simple_invites/     # Persistente Daten (DB, Schlüssel, etc.)
├── requirements.txt         # Python-Abhängigkeiten
├── Dockerfile               # Docker-Setup
└── docker-compose.yml       # Docker Compose Konfiguration
```

## 🛠️ Konfiguration

- **WhatsApp-Benachrichtigungen**:
  - Telefonnummer und API-Key in den Admin-Einstellungen hinterlegen.
  - CallMeBot wird verwendet, um Nachrichten zu versenden.

- **Passwortschutz**:
  - Beim ersten Login wird eine Passwortänderung erzwungen.
  - Passwörter werden sicher gehasht gespeichert.

- **SECRET_KEY**:
  - Für Produktion muss ein sicherer Schlüssel gesetzt werden (Umgebungsvariable oder automatische Generierung beim ersten Start).
  - Wird im Volume gespeichert und bleibt beim Neustart erhalten.

## 📖 Hinweise

- **QR-Codes**:
  - QR-Codes werden im Ordner `static/qrcodes/` gespeichert.
  - Beim Löschen einer Einladung wird der zugehörige QR-Code automatisch entfernt.

- **Datenbank**:
  - Die SQLite-Datenbank und alle Einstellungen werden im Ordner `data/simple_invites/` gespeichert.
  - Für produktive Umgebungen kann eine andere Datenbank (z. B. PostgreSQL) konfiguriert werden.

---

Mit ❤️ und GitHub Copilot gebaut für das 150-jährige Jubiläum der Freiwilligen Feuerwehr Windischletten – oder jedes andere Event.