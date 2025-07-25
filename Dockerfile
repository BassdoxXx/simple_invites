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
RUN pip install gunicorn whitenoise

# Kopiere den gesamten Code
COPY . .

# Copy built CSS from node build stage
COPY --from=build-stage /app/app/static/css/styles.css /app/app/static/css/

# Make sure static directories exist with proper permissions
RUN mkdir -p /app/app/static/css /app/app/static/js
RUN chmod -R 755 /app/app/static

# Debug: List static files to ensure they exist
RUN ls -la /app/app/static/css/
RUN ls -la /app/app/static/js/

# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production

# Create a small script to run the app
RUN echo 'from app.main import app as application' > wsgi.py

# Add whitenoise to requirements if not already present
RUN if ! grep -q "whitenoise" requirements.txt; then echo "whitenoise" >> requirements.txt; fi

# Starte die Anwendung with appropriate static file configuration
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "wsgi:application", "--log-level=debug"]