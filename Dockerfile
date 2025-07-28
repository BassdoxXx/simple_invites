
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Kopiere den gesamten Code
COPY . .

# Kopiere das gesamte static-Verzeichnis an die richtige Stelle
COPY app/static /app/static
# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production

# Starte die Anwendung
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app"]