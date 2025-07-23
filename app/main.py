# Diese Datei ist nicht mehr nötig
# Der neue Einstiegspunkt ist app.py im Projektroot


from app import create_app

# Für Rückwärtskompatibilität
app = create_app()

if __name__ == "__main__":
    print("⚠️  Warnung: Verwende app.py im Projektroot anstatt app/main.py")
    app.run(host="0.0.0.0", port=5000, debug=False)