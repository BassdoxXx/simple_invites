"""
Hilfsfunktion um statische Dateien zu finden und zu prüfen
"""
import os
from flask import current_app

def check_static_files():
    """Überprüft, ob alle wichtigen statischen Dateien existieren"""
    static_folder = current_app.static_folder
    critical_files = [
        "css/styles.css",
        "js/admin.js",
        "js/charts.js"
    ]
    
    results = {}
    for file_path in critical_files:
        full_path = os.path.join(static_folder, file_path)
        exists = os.path.exists(full_path)
        results[file_path] = {
            "exists": exists,
            "path": full_path,
            "size": os.path.getsize(full_path) if exists else None
        }
    
    return results

def debug_static_files():
    """Debug-Funktion für statische Dateien"""
    static_folder = current_app.static_folder
    
    # Zeige Verzeichnisstruktur an
    dir_structure = {}
    if os.path.exists(static_folder):
        for root, dirs, files in os.walk(static_folder):
            rel_path = os.path.relpath(root, static_folder)
            if rel_path == '.':
                rel_path = ''
            dir_structure[rel_path] = files
    
    return {
        "static_folder": static_folder,
        "exists": os.path.exists(static_folder),
        "directory_structure": dir_structure,
        "critical_files": check_static_files()
    }
