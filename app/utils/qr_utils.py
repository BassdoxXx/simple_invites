import os
import qrcode
import re

# Basispfad des Projekts bestimmen
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
QR_DIR = os.path.join(BASE_DIR, 'app', 'static', 'qrcodes')

def generate_qr(url, path, token):
    """
    Erzeugt einen QR-Code für den gegebenen Link und speichert ihn im static/qrcodes-Ordner.
    Der Dateiname ist immer verein_token.png, wobei Leerzeichen durch Unterstriche ersetzt werden.

    Args:
        url (str): Die vollständige URL, die in den QR-Code eingebettet wird.
        path (str): Vereinsname.
        token (str): Token für die Einladung.

    Returns:
        str: Relativer Pfad zur gespeicherten QR-Code-Datei für Flask (z.B. 'qrcodes/Verein_token.png').
    """
    # Vereinsname und Token für Dateinamen aufbereiten
    safe_verein = re.sub(r'\s+', '_', path.strip())
    safe_token = token.strip()
    filename = f"{safe_verein}_{safe_token}.png"

    os.makedirs(QR_DIR, exist_ok=True)
    full_path = os.path.join(QR_DIR, filename)
    img = qrcode.make(url)
    img.save(full_path)
    return f"qrcodes/{filename}"