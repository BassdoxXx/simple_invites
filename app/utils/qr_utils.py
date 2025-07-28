import os
import qrcode
import re
from app.models import db, Invite

# Basispfad des Projekts bestimmen
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
QR_DIR = os.path.join(BASE_DIR, 'app', 'static', 'qrcodes')

# In Docker-Umgebung sicherstellen, dass der Ordner existiert
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr(url, path, token, invite_id=None):
    """
    Erzeugt einen QR-Code für den gegebenen Link und speichert ihn im static/qrcodes-Ordner.
    Der Dateiname ist immer verein_token.png, wobei Leerzeichen durch Unterstriche ersetzt werden.
    Wenn eine invite_id angegeben wird, wird der Pfad in der Datenbank gespeichert.

    Args:
        url (str): Die vollständige URL, die in den QR-Code eingebettet wird.
        path (str): Vereinsname.
        token (str): Token für die Einladung.
        invite_id (int, optional): ID der Einladung in der Datenbank.

    Returns:
        str: Relativer Pfad zur gespeicherten QR-Code-Datei für Flask (z.B. 'qrcodes/Verein_token.png').
    """
    # Vereinsname und Token für Dateinamen aufbereiten
    safe_verein = re.sub(r'\s+', '_', path.strip())
    safe_token = token.strip()
    filename = f"{safe_verein}_{safe_token}.png"

    os.makedirs(QR_DIR, exist_ok=True)
    full_path = os.path.join(QR_DIR, filename)
    
    # QR-Code mit höherer Auflösung und Fehlerkorrektur erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(full_path)
    
    rel_path = f"qrcodes/{filename}"
    
    # Wenn eine invite_id angegeben wurde, speichere den QR-Code-Pfad in der Datenbank
    if invite_id is not None:
        invite = Invite.query.get(invite_id)
        if invite:
            invite.qr_code_path = rel_path
            db.session.commit()
    
    return rel_path

def regenerate_qr_for_all_invites(base_url):
    """
    Generiert QR-Codes für alle Einladungen in der Datenbank neu.
    Nützlich nach einem Import oder wenn sich die URL-Struktur geändert hat.
    
    Args:
        base_url (str): Die Basis-URL für die Einladungen.
    
    Returns:
        int: Anzahl der generierten QR-Codes.
    """
    invites = Invite.query.all()
    count = 0
    
    for invite in invites:
        url = f"{base_url}/respond/{invite.token}"
        generate_qr(url, invite.verein, invite.token, invite.id)
        count += 1
    
    return count