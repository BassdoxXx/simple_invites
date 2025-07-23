"""
Utilities for CSV import and export operations.
"""

import csv
import io
import random
import string
from flask import flash, redirect, url_for, request, Response
from app.models import Invite, Response as InviteResponse, db
from datetime import datetime

def validate_csv_file(csv_file):
    """
    Validates that the uploaded file is a valid CSV file.
    
    Args:
        csv_file: The uploaded file object from request.files
        
    Returns:
        tuple: (is_valid, content, dialect, error_redirect)
            - is_valid: Boolean indicating if the file is valid
            - content: The file content if valid, None otherwise
            - dialect: The CSV dialect if valid, None otherwise
            - error_redirect: A redirect response if validation failed, None if successful
    """
    if csv_file.filename == '':
        flash("Keine Datei ausgewählt.", "danger")
        return False, None, None, redirect(url_for("admin.create_invite"))
    
    # 1. Überprüfe die Dateierweiterung
    if not csv_file.filename.lower().endswith('.csv'):
        flash("Nur CSV-Dateien sind erlaubt (.csv).", "danger")
        return False, None, None, redirect(url_for("admin.create_invite"))
        
    # 2. Überprüfe den MIME-Type (Content-Type)
    allowed_mime_types = ['text/csv', 'text/plain', 'application/csv', 'application/vnd.ms-excel']
    if csv_file.content_type not in allowed_mime_types:
        flash(f"Die Datei hat einen ungültigen Typ: {csv_file.content_type}. Erlaubt sind nur CSV-Dateien.", "danger")
        return False, None, None, redirect(url_for("admin.create_invite"))
        
    # 3. Überprüfe die Dateigröße (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in Bytes
    if csv_file.content_length > max_size:
        flash("Die Datei ist zu groß. Maximale Dateigröße ist 5MB.", "danger")
        return False, None, None, redirect(url_for("admin.create_invite"))
    
    # Lese CSV-Datei
    try:
        content = csv_file.read().decode('utf-8-sig')  # UTF-8 mit BOM unterstützen
        
        # Validiere den CSV-Inhalt mit dem CSV-Sniffer
        if not content.strip():
            flash("Die Datei ist leer.", "danger")
            return False, None, None, redirect(url_for("admin.create_invite"))
        
        # Verwende den CSV-Sniffer, um zu überprüfen, ob es sich wirklich um CSV handelt
        sniffer = csv.Sniffer()
        try:
            # Überprüft, ob die Datei ein CSV-Format hat
            is_csv = sniffer.has_header(content[:1024]) or sniffer.sniff(content[:1024])
            dialect = sniffer.sniff(content[:1024])
        except csv.Error:
            flash("Die Datei scheint kein gültiges CSV-Format zu haben.", "danger")
            return False, None, None, redirect(url_for("admin.create_invite"))
        
        csv_data = csv.reader(io.StringIO(content), dialect)
        
        # Validiere, dass die Datei nur aus Textzeilen besteht
        # und keine ausführbaren oder binären Daten enthält
        try:
            for row_num, row in enumerate(csv_data):
                if row_num > 100:  # Maximal 100 Zeilen prüfen
                    break
                
                for cell in row:
                    if not isinstance(cell, str):
                        raise ValueError("Nicht-Text-Daten gefunden")
                    
                    # Überprüfe auf potenziell gefährliche Inhalte
                    if any(char in cell for char in '<>&;[]'):
                        flash("Die CSV-Datei enthält unerlaubte Sonderzeichen.", "danger")
                        return False, None, None, redirect(url_for("admin.create_invite"))
            
            return True, content, dialect, None
            
        except:
            flash("Die Datei enthält ungültige Daten und konnte nicht verarbeitet werden.", "danger")
            return False, None, None, redirect(url_for("admin.create_invite"))
            
    except UnicodeDecodeError:
        flash("Die Datei konnte nicht als Text gelesen werden. Bitte stellen Sie sicher, dass es sich um eine valide CSV-Datei handelt.", "danger")
        return False, None, None, redirect(url_for("admin.create_invite"))


def process_csv_import(content, dialect, has_header, base_url):
    """
    Process the CSV content and create invitations.
    
    Args:
        content: The CSV file content
        dialect: The CSV dialect to use
        has_header: Boolean indicating if the CSV has a header
        base_url: The base URL for invitation links
        
    Returns:
        int: The number of successfully imported invitations
    """
    csv_data = csv.reader(io.StringIO(content), dialect)
    max_imports = 500
    imported_count = 0
    duplicate_count = 0
    
    # Bestehende Vereine in der Datenbank abrufen (als Set für schnellere Suche)
    existing_vereine = {invite.verein.lower() for invite in Invite.query.all()}
    
    # Überspringe Header, wenn vorhanden
    first_row = None
    if has_header:
        first_row = next(csv_data, None)
    
    # Bestimme den Index der Vereinsspalte, falls ein Header existiert
    verein_index = 0
    if has_header and first_row:
        for i, header in enumerate(first_row):
            if header.lower().strip() == 'verein':
                verein_index = i
                break
    
    for row in csv_data:
        if not row or len(row) <= verein_index:  # Überspringe leere oder unvollständige Zeilen
            continue
        
        # Nehme den Wert aus der Vereinsspalte
        verein = row[verein_index].strip()
        
        if not verein:  # Überspringe leere Namen
            continue
        
        # Begrenze die Anzahl der Importe
        if imported_count >= max_imports:
            flash(f"Import auf {max_imports} Einträge begrenzt. Bitte teilen Sie größere Dateien auf.", "warning")
            break
        
        # Prüfe, ob der Verein bereits existiert (case-insensitive Prüfung)
        if verein.lower() in existing_vereine:
            duplicate_count += 1
            continue
            
        # Verein zur Liste der existierenden Vereine hinzufügen
        existing_vereine.add(verein.lower())
            
        # Generiere einen einzigartigen Token
        token = generate_unique_token()
        
        # Erstelle die Einladung
        invite_url = f"{base_url}/respond/{token}"
        new_invite = Invite(
            verein=verein,
            token=token,
            link=invite_url
        )
        db.session.add(new_invite)
        imported_count += 1
    
    db.session.commit()
    
    # Wenn doppelte Einträge gefunden wurden, Information anzeigen
    if duplicate_count > 0:
        flash(f"{duplicate_count} Einträge wurden übersprungen, da sie bereits existieren.", "warning")
        
    return imported_count


def generate_unique_token():
    """
    Generate a unique 8-character token for an invitation.
    
    Returns:
        str: A unique token
    """
    # Generiere einen 8-stelligen alphanumerischen Token (kleinbuchstaben und Zahlen)
    token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Stelle sicher, dass der Token einzigartig ist
    while Invite.query.filter_by(token=token).first():
        token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    return token


def generate_all_invites_csv(invites, responses, get_full_link_func):
    """
    Generiert eine CSV-Datei mit allen Einladungen und deren Antworten.
    
    Args:
        invites: Liste aller Einladungen
        responses: Dictionary mit Token als Schlüssel und Response-Objekt als Wert
        get_full_link_func: Funktion, die einen vollen URL-Link für eine Einladung erzeugt
        
    Returns:
        Response-Objekt mit CSV-Datei
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow([
        "Verein", "Tischnummer", "Link", "Antwort", 
        "Personen", "Zuletzt aktualisiert"
    ])
    
    # Sortiere Einladungen alphabetisch nach Vereinsname
    sorted_invites = sorted(invites, key=lambda x: x.verein.lower())
    
    for invite in sorted_invites:
        res = responses.get(invite.token)
        full_link = get_full_link_func(invite.token)
        
        writer.writerow([
            invite.verein,
            invite.tischnummer,
            full_link,
            res.attending if res else "",
            res.persons if res else "",
            res.timestamp.strftime('%d.%m.%Y %H:%M') if res and res.timestamp else ""
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=einladungen.csv"}
    )


def generate_single_invite_csv(invite, response, get_full_link_func):
    """
    Generiert eine CSV-Datei mit einer einzelnen Einladung und deren Antwort.
    
    Args:
        invite: Das Einladungs-Objekt
        response: Das Response-Objekt (kann None sein)
        get_full_link_func: Funktion, die einen vollen URL-Link für eine Einladung erzeugt
        
    Returns:
        Response-Objekt mit CSV-Datei
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow([
        "Verein", "Tischnummer", "Link", "Antwort", 
        "Personen", "Zuletzt aktualisiert"
    ])
    
    full_link = get_full_link_func(invite.token)
    writer.writerow([
        invite.verein,
        invite.tischnummer,
        full_link,
        response.attending if response else "",
        response.persons if response else "",
        response.timestamp.strftime('%d.%m.%Y %H:%M') if response and response.timestamp else ""
    ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=einladung_{invite.verein}_{invite.token}.csv"}
    )
