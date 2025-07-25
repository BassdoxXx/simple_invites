FROM node:20-slim as build-stage

WORKDIR /app
COPY package.json tailwind.config.js ./
COPY app/static/css/src ./app/static/css/src

# Install Node dependencies and build CSS
RUN npm install
RUN npm run build:css
RUN mkdir -p /app/static-files/css /app/static-files/js
RUN cp -a /app/app/static/css/styles.css /app/static-files/css/

FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Create a dedicated static directory with all files
RUN mkdir -p /static-files-backup

# Copy static files first to ensure they're included
COPY app/static/css/styles.css /static-files-backup/css/
COPY app/static/js/*.js /static-files-backup/js/

# Kopiere den gesamten Code
COPY . .

# Explicitly ensure all necessary static directories exist
RUN mkdir -p /app/app/static/css /app/app/static/js /app/app/static/fonts /app/app/static/images /app/app/static/pdfs /app/app/static/qrcodes

# Restore static files from backup
RUN cp -f /static-files-backup/css/styles.css /app/app/static/css/
RUN cp -f /static-files-backup/js/* /app/app/static/js/

# Also copy from build stage as fallback
COPY --from=build-stage /app/static-files/css/styles.css /app/app/static/css/

# Create empty files to ensure static directories are not empty
RUN touch /app/app/static/fonts/.keep
RUN touch /app/app/static/images/.keep
RUN touch /app/app/static/pdfs/.keep
RUN touch /app/app/static/qrcodes/.keep

# Simple shell script to copy QR codes if they exist
RUN echo '#!/bin/sh\nif [ -d "app/static/qrcodes" ]; then\n  cp -r app/static/qrcodes/* /app/app/static/qrcodes/ 2>/dev/null || echo "No QR codes to copy"\nfi\nif [ -d "app/static/pdfs" ]; then\n  cp -r app/static/pdfs/* /app/app/static/pdfs/ 2>/dev/null || echo "No PDFs to copy"\nfi' > /app/copy_static.sh && chmod +x /app/copy_static.sh

# Execute the script (will silently continue if directories don't exist)
RUN /app/copy_static.sh

# Debug: List contents of critical directories
RUN echo "CSS directory:" && ls -la /app/app/static/css/
RUN echo "JS directory:" && ls -la /app/app/static/js/

# Create a static file verification script
RUN echo '#!/bin/sh\necho "Checking for critical static files..."\nMISSING=0\nfor f in /app/app/static/css/styles.css /app/app/static/js/admin.js /app/app/static/js/charts.js; do\n  if [ ! -f "$f" ]; then\n    echo "ERROR: Missing $f"\n    MISSING=1\n  else\n    echo "Found $f ($(wc -c < $f) bytes)"\n  fi\ndone\necho "Directory structure:"\nfind /app/app/static -type d | sort\necho "All static files:"\nfind /app/app/static -type f | sort\nif [ $MISSING -eq 1 ]; then\n  echo "ERROR: Some critical static files are missing!"\nelse\n  echo "SUCCESS: All critical static files exist."\nfi' > /app/check_static.sh

# Make script executable
RUN chmod +x /app/check_static.sh

# Make sure static directories have proper permissions
RUN chmod -R 755 /app/app/static

# Add explicit permissions for CSS and JS files
RUN find /app/app/static -name "*.css" -exec chmod 644 {} \; 2>/dev/null || true
RUN find /app/app/static -name "*.js" -exec chmod 644 {} \; 2>/dev/null || true

# Run the verification script
RUN /app/check_static.sh

# Create an init script that ensures static files exist at startup
RUN echo '#!/bin/sh\necho "Ensuring static files exist on startup..."\n# Check if static files exist, if not restore from backup\nif [ ! -f "/app/app/static/css/styles.css" ]; then\n  echo "Restoring missing styles.css"\n  cp -f /static-files-backup/css/styles.css /app/app/static/css/\nfi\nfor js_file in /static-files-backup/js/*.js; do\n  filename=$(basename "$js_file")\n  if [ ! -f "/app/app/static/js/$filename" ]; then\n    echo "Restoring missing $filename"\n    cp -f "$js_file" /app/app/static/js/\n  fi\ndone\necho "Static file check complete."' > /app/ensure_static.sh
RUN chmod +x /app/ensure_static.sh

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

# Final static directory check to ensure all files are present
RUN echo "Final static directory check:" && find /app/app/static -type f | sort

# Create entrypoint script that ensures static files before starting
RUN echo '#!/bin/sh\n/app/ensure_static.sh\nexec gunicorn --config gunicorn.conf.py wsgi:application' > /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Starte die Anwendung with appropriate static file configuration
CMD ["/app/entrypoint.sh"]