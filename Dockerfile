
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Kopiere den gesamten Code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY tests/ ./tests/
COPY *.py ./
COPY *.md ./
COPY *.ini ./
COPY *.sh ./

# Erstelle fehlende Verzeichnisse und setze Berechtigungen für dynamische Dateien
RUN mkdir -p app/static app/static/css app/static/js app/static/images app/static/pdfs app/static/qrcodes app/static/fonts instance data/simple_invites
RUN chmod -R 777 app/static/pdfs app/static/qrcodes instance data

# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production
# Der Wert dieser Variable sollte beim Build oder Run überschrieben werden
ENV APP_HOSTNAME=http://localhost:5000

# Starte die Anwendung
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app"]