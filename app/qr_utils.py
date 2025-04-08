import os
import qrcode

# Basispfad des Projekts bestimmen
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
QR_DIR = os.path.join(BASE_DIR, 'static', 'qrcodes')

def generate_qr(link, filename):
    """
    Erzeugt einen QR-Code für den gegebenen Link und speichert ihn im static/qrcodes-Ordner.
    Diese Funktion stellt sicher, dass der Zielordner vorhanden ist und gibt den Pfad zurück,
    der in HTML-Vorlagen verwendet werden kann.

    Args:
        link (str): Die vollständige URL, der in den QR-Code eingebettet wird.
        filename (str): Der Dateiname (z.B. Token) unter dem der QR-Code gespeichert wird.

    Returns:
        str: Relativer Pfad zur gespeicherten QR-Code-Datei für Flask (z.B. 'static/qrcodes/abc123').
    """
    os.makedirs(QR_DIR, exist_ok=True)
    full_path = os.path.join(QR_DIR, filename)
    img = qrcode.make(link)
    img.save(full_path)
    return f"static/qrcodes/{filename}"
