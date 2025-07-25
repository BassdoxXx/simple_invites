FROM node:20-slim as build-stage

WORKDIR /app
COPY package.json tailwind.config.js ./
COPY app/static/css/src ./app/static/css/src

# Install Node dependencies and build CSS
RUN npm install
RUN npm run build:css

FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Kopiere den gesamten Code
COPY . .

# Copy built CSS from build stage
COPY --from=build-stage /app/app/static/css/styles.css ./app/static/css/

# Ensure static files have correct permissions and create missing directories if needed
RUN mkdir -p /app/app/static/css /app/app/static/js
RUN chmod -R 755 /app/app/static

# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production

# Starte die Anwendung
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app.main:app"]