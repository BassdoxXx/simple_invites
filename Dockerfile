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

# Copy built CSS from node build stage
COPY --from=build-stage /app/app/static/css/styles.css /app/app/static/css/

# Ensure all static files are copied correctly
COPY app/static/ /app/app/static/
RUN ls -la /app/app/static/css/
RUN ls -la /app/app/static/js/

# Make sure static directories have proper permissions
RUN chmod -R 755 /app/app/static

# Add explicit permissions for CSS and JS files
RUN find /app/app/static -name "*.css" -exec chmod 644 {} \;
RUN find /app/app/static -name "*.js" -exec chmod 644 {} \;

# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production

# Create a small script to run the app
RUN echo 'from app.main import app as application' > wsgi.py

# Ensure all dependencies are installed

# Copy gunicorn config
COPY gunicorn.conf.py /app/gunicorn.conf.py

# Set environment variables for better debugging
ENV PYTHONUNBUFFERED=1

# Starte die Anwendung with appropriate static file configuration
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:application"]