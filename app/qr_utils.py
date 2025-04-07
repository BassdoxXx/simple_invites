import os
import qrcode

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
QR_DIR = os.path.join(BASE_DIR, 'static', 'qrcodes')

def generate_qr(link, filename):
    os.makedirs(QR_DIR, exist_ok=True)  # Stelle sicher, dass der Ordner existiert
    full_path = os.path.join(QR_DIR, filename)
    img = qrcode.make(link)
    img.save(full_path)
    # Pfad relativ zum static-Folder für Flask:
    return f"static/qrcodes/{filename}"
