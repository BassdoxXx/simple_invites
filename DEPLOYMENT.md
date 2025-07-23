# Deployment Guide für ffw-dockersetup

## 🚀 Setup für Production Environment

### 1. Vorbereitung auf dem Server

```bash
# Navigiere zu deinem ffw-dockersetup Verzeichnis
cd ~/ffw-dockersetup

# Erstelle die notwendigen Datenordner
mkdir -p data/simple_invites
mkdir -p configs/simple_invites

# Setze die richtigen Berechtigungen
chmod 755 data/simple_invites
```

### 2. Docker Compose Configuration

Füge diesen Service zu deiner `docker-compose.yaml` hinzu:

```yaml
  simple_invites:
    image: bassdoxxx/simple_invites:latest
    container_name: simple_invites
    restart: unless-stopped
    volumes:
      # Persistente Daten (SQLite DB, Static Files)
      - ./data/simple_invites:/app/instance
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SIMPLE_INVITES_SECRET_KEY:-your_secret_key_here}
      - APP_HOSTNAME=https://invites.ffw-windischletten.de
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    networks:
      - core_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 1m30s
      timeout: 10s
      retries: 3
```

### 3. Environment Variables

Füge zu deiner `.env` Datei hinzu:

```bash
# Simple Invites Configuration
SIMPLE_INVITES_SECRET_KEY=your_super_secret_key_here_change_this
```

### 4. Container starten

```bash
# Container starten
docker-compose up -d simple_invites

# Logs überprüfen
docker-compose logs -f simple_invites
```

### 5. Erste Anmeldung

- URL: `https://invites.ffw-windischletten.de`
- Username: `admin`
- Password: `changeme`
- ⚠️ **Wichtig**: Ändere das Passwort sofort nach der ersten Anmeldung!

## 📁 Datenstruktur

```
ffw-dockersetup/
├── data/
│   └── simple_invites/           # Persistente Daten
│       ├── simple_invites.db     # SQLite Datenbank
│       └── secret_key.txt        # Auto-generierter Secret Key
├── configs/
│   └── simple_invites/           # Konfigurationsdateien (optional)
└── docker-compose.yaml
```

## 🔧 Wartung

### Container neu starten
```bash
docker-compose restart simple_invites
```

### Logs einsehen
```bash
docker-compose logs -f simple_invites
```

### Image updaten
```bash
docker-compose pull simple_invites
docker-compose up -d simple_invites
```

### Datenbank-Backup
```bash
# Backup der SQLite Datenbank
cp data/simple_invites/simple_invites.db data/simple_invites/simple_invites.db.backup.$(date +%Y%m%d_%H%M%S)
```

## 🛠️ Troubleshooting

### Container startet nicht
```bash
# Überprüfe die Logs
docker-compose logs simple_invites

# Überprüfe die Berechtigungen
ls -la data/simple_invites/
```

### Datenbank Probleme
```bash
# Container stoppen
docker-compose stop simple_invites

# Datenbank löschen (alle Daten gehen verloren!)
rm data/simple_invites/simple_invites.db

# Container neu starten
docker-compose up -d simple_invites
```

## 📋 Features

- ✅ **Einfach**: SQLite Datenbank, keine externe DB nötig
- ✅ **Persistent**: Alle Daten bleiben bei Container-Updates erhalten
- ✅ **Sicher**: Automatische Secret Key Generierung
- ✅ **Portabel**: Läuft überall wo Docker läuft
- ✅ **Wartungsarm**: Watchtower Auto-Updates unterstützt
