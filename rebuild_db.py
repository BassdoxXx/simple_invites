# rebuild_db.py
import os
import sqlite3
import shutil

# Pfad zur Datenbank
db_path = os.path.join('instance', 'simple_invites.db')

# Überprüfen ob die Datenbank existiert
if os.path.exists(db_path):
    print(f"Datenbank gefunden unter: {os.path.abspath(db_path)}")
    try:
        # Sicherheitskopie erstellen
        backup_path = os.path.join('instance', 'simple_invites.db.bak')
        shutil.copy2(db_path, backup_path)
        print(f"Backup erstellt: {backup_path}")
        
        # Datei löschen
        os.remove(db_path)
        print(f"Datenbank gelöscht!")
    except Exception as e:
        print(f"Fehler: {e}")
else:
    print("Keine bestehende Datenbank gefunden.")

print("\nStarte die Anwendung neu mit 'python -m app.main' um die Datenbank neu zu erstellen.")