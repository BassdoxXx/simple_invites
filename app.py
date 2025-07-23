#!/usr/bin/env python3
"""
Simple Invites - Einfache Einladungsverwaltung für Feuerwehren
Haupteinstiegspunkt für die Flask-Anwendung
"""

from app import create_app

# Flask-App erstellen
app = create_app()

if __name__ == "__main__":
    # Für lokale Entwicklung
    app.run(debug=False, host="0.0.0.0", port=5000)
