FROM python:3.11-slim

WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installiere Python-Abhängigkeiten
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Kopiere den Anwendungscode
COPY app/ ./app/
COPY app.py .

# Persistente Datenordner erstellen
RUN mkdir -p /app/instance

# Port freigeben
EXPOSE 5000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Non-root User für Sicherheit
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Starte die Anwendung mit Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]