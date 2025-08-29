"""
Utilities for PDF invitation generation.
"""

import os
import glob
import time
from fpdf import FPDF
from datetime import datetime, timedelta
from flask import current_app
from app.utils.settings_utils import get_base_url

# Logger setup
import logging
logger = logging.getLogger(__name__)

# Base directory of project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PDF_DIR = os.path.join(BASE_DIR, 'app', 'static', 'pdfs')
LOGO_PATH = os.path.join(BASE_DIR, 'app', 'static', 'images', 'logo.png')

# Stellen Sie sicher, dass das Verzeichnis existiert - wichtig für Docker-Container
os.makedirs(PDF_DIR, exist_ok=True)
if not os.path.exists(LOGO_PATH):
    logger.warning(f"Logo nicht gefunden unter {LOGO_PATH}")
    # Log auch Pfade für Debug-Zwecke
    logger.debug(f"BASE_DIR: {BASE_DIR}")
    logger.debug(f"PDF_DIR: {PDF_DIR}")

def cleanup_old_pdf_files(max_age_minutes=15):
    """
    Löscht PDF-Dateien, die älter als max_age_minutes sind.
    
    Args:
        max_age_minutes: Maximales Alter in Minuten, bevor Dateien gelöscht werden
    """
    try:
        # Versuche, den konfigurierten Wert aus der App-Konfiguration zu lesen (falls vorhanden)
        try:
            if current_app and current_app.config and 'PDF_CLEANUP_MINUTES' in current_app.config:
                max_age_minutes = int(current_app.config['PDF_CLEANUP_MINUTES'])
        except (RuntimeError, ValueError, TypeError):
            # Wenn kein App-Kontext oder ungültiger Wert, behalte den Standard bei
            pass
            
        # Alle PDF-Dateien im Verzeichnis finden
        pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
        
        # Aktuelle Zeit für den Vergleich
        now = time.time()
        
        # Zähle gelöschte Dateien
        deleted_count = 0
        error_count = 0
        
        # Gehe durch alle PDF-Dateien
        for pdf_file in pdf_files:
            try:
                # Ermittle das Änderungsdatum der Datei
                file_mod_time = os.path.getmtime(pdf_file)
                
                # Wenn die Datei älter als max_age_minutes ist, lösche sie
                if now - file_mod_time > max_age_minutes * 60:
                    try:
                        os.remove(pdf_file)
                        deleted_count += 1
                    except PermissionError:
                        # Datei ist wahrscheinlich noch in Benutzung - überspringen
                        error_count += 1
                        pass
                    except Exception as e:
                        error_count += 1
                        try:
                            current_app.logger.error(f"Error deleting PDF file {pdf_file}: {e}")
                        except:
                            logger.error(f"Error deleting PDF file {pdf_file}: {e}")
            except Exception as e:
                # Fehler beim Lesen der Datei-Metadaten überspringen
                logger.warning(f"Error reading file metadata for {pdf_file}: {e}")
                continue
                
        # Logge nur, wenn tatsächlich Dateien gelöscht wurden
        if deleted_count > 0:
            try:
                current_app.logger.info(f"PDF cleanup: deleted {deleted_count} files older than {max_age_minutes} minutes")
            except:
                logger.info(f"PDF cleanup: deleted {deleted_count} files older than {max_age_minutes} minutes")
                
        # Logge Fehler nur, wenn welche aufgetreten sind
        if error_count > 0:
            try:
                current_app.logger.warning(f"PDF cleanup: encountered {error_count} errors while trying to delete files")
            except:
                logger.warning(f"PDF cleanup: encountered {error_count} errors while trying to delete files")
                
    except Exception as e:
        try:
            current_app.logger.error(f"Error during PDF cleanup: {e}")
        except:
            logger.error(f"Error during PDF cleanup: {e}")

class InvitationPDF(FPDF):
    """Custom PDF class for invitation generation strictly according to DIN 5008"""
    
    def __init__(self, orientation='P', unit='mm', format='A4', settings=None):
        super().__init__(orientation, unit, format)
        # Store settings for later use in footer
        self.settings = settings
        # DIN 5008 standard margins: 2.5cm left, at least 1cm right
        self.set_margins(25, 20, 10)  # left, top, right margins
        self.set_auto_page_break(auto=True, margin=20)  # bottom margin
        # DIN 5008 recommends Arial 11pt or Times New Roman 12pt
        self.set_font('Arial', '', 11)  # Default font
        
    def add_folding_marks(self):
        """Adds the DIN 5008 standard folding marks to the page"""
        # Save current line width setting
        line_width = self.line_width
        
        # Set thin light gray line for folding marks
        self.set_line_width(0.1)
        self.set_draw_color(200, 200, 200)
        
        # First fold mark at 105mm from top (for DIN lang envelope)
        self.line(5, 105, 8, 105)
        
        # Second fold mark at 210mm from top (for folding in thirds)
        self.line(5, 210, 8, 210)
        
        # Restore original settings
        self.set_line_width(line_width)
        # Reset to default black color
        self.set_draw_color(0)

    def header(self):
        # Briefkopf - gemäß DIN 5008 maximal 7 Zeilen für Name, Anschrift, Telefon, E-Mail
        try:
            if os.path.exists(LOGO_PATH) and os.path.isfile(LOGO_PATH) and os.path.getsize(LOGO_PATH) > 0:
                # Get the width of the page
                page_width = self.w
                # Logo dimensions - moderate size to fit with other header elements
                logo_width = 55
                # Position logo in top right area
                self.image(LOGO_PATH, x=page_width-70, y=0, w=logo_width)
                logger.debug(f"Logo successfully added from {LOGO_PATH}")
        except Exception as e:
            # Log the error but continue without the logo
            logger.error(f"Could not add logo: {e}")
            
        # Add folding marks according to DIN 5008
        self.add_folding_marks()

    def footer(self):
        """Footer with dynamic contact information and legally required details according to DIN 5008"""
        # First try to use settings from the instance if available
        if hasattr(self, 'settings') and self.settings:
            settings = self.settings
        else:
            # Try to get settings from Flask app config as fallback
            try:
                from flask import current_app
                settings = current_app.config.get('CURRENT_SETTINGS', {})
            except:
                settings = {}
        
        # Get values from settings with fallbacks
        vereins_name = settings.get('vereins_name', "Freiwillige Feuerwehr ")
        contact_email = settings.get('contact_email', "info@feuerwehren.bayern")
        website = settings.get('website', "www.feuerwehren.bayern")
        
        # Brieffuß - gemäß DIN 5008 mit gesetzlich vorgeschriebenen Informationen
        self.set_y(-25)  # 25mm from bottom
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)  # Black text
        
        # Footer with all required business information using dynamic settings
        # Calculate center of page (not just printable area) to get true centering
        page_center = self.w / 2
        # Get the width of the text to center properly
        vereins_width = self.get_string_width(vereins_name)
        contact_width = self.get_string_width(f"{website} | {contact_email}")
        
        # Set x position to center the text on the page, not just within printable area
        self.set_x(page_center - vereins_width / 2)
        self.cell(vereins_width, 4, f"{vereins_name}", 0, 1)
        
        self.set_x(page_center - contact_width / 2)
        self.cell(contact_width, 4, f"{website} | {contact_email}", 0, 1)

def generate_invitation_pdf(invite, settings):
    """
    Generiert ein PDF für eine Einladung basierend auf einem Layout-Template.
    Erzeugt dafür temporär einen QR-Code, der nach der PDF-Erstellung wieder gelöscht wird.
    
    Args:
        invite: Das Einladungs-Objekt aus der Datenbank
        settings: Dictionary mit Einstellungen für die Veranstaltung
    
    Returns:
        str: Pfad zur generierten PDF-Datei
    """
    # Stelle sicher, dass das PDF-Verzeichnis existiert
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Lösche alte PDF-Dateien, um Speicherplatz zu sparen
    cleanup_old_pdf_files()
    
    # Store settings in current_app.config to make them available to the footer method
    try:
        from flask import current_app
        # Update the CURRENT_SETTINGS with the passed settings
        current_app.config['CURRENT_SETTINGS'] = settings
    except:
        pass
    
    # Vorbereitung: Veranstaltungsinformationen aus den Settings extrahieren
    vereins_name = settings.get("vereins_name", "")
    event_name = settings.get("event_name", "")
    event_date = settings.get("event_date", "")
    event_location = settings.get("event_location", "")
    event_time = settings.get("event_time", "")
    invite_header = settings.get("invite_header", "")
    
    # Formatiere das Datum, falls vorhanden
    formatted_date = ""
    if event_date:
        try:
            date_obj = datetime.strptime(event_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except ValueError:
            formatted_date = event_date
    
    # PDF erstellen with settings
    pdf = InvitationPDF(settings=settings)
    pdf.add_page()
    
    # Dynamische Kontaktdaten aus den Einstellungen holen
    contact_address = settings.get("contact_address", "Musterstraße 123, 12345 Musterstadt")
    
    # Adresse für die Rücksendeadresse vorbereiten (nur Straße und Ort)
    address_parts = contact_address.split(',')
    short_address = address_parts[0] if len(address_parts) > 0 else contact_address
    
    # Nur die Rücksendeadresse (kleinere Schrift, im Briefkopf)
    # Wir entfernen den Briefkopf mit dem umrandeten Absender oben
    pdf.set_xy(25, 45)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 3, f"{vereins_name} · {short_address} · {address_parts[1].strip() if len(address_parts) > 1 else ''}", 0, 1, 'L')
    
    # Anschriftenfeld - genau nach DIN 5008 (40 x 85 mm links)
    empfaenger_y = 50  # Startposition für den Empfänger
    
    # Empfänger (eingeladener Verein) - präzise DIN 5008-konforme Formatierung
    pdf.set_xy(25, empfaenger_y)
    pdf.set_font('Arial', '', 11)
    if invite.ansprechpartner:
        pdf.cell(0, 5, invite.ansprechpartner, 0, 1)
    pdf.cell(0, 5, invite.verein, 0, 1)
    if invite.strasse:
        pdf.cell(0, 5, invite.strasse, 0, 1)
    if invite.plz and invite.ort:
        pdf.cell(0, 5, f"{invite.plz} {invite.ort}", 0, 1)
    
    # Infoblock auf der rechten Seite - nur Datum gemäß DIN 5008
    info_x = pdf.w - 80  # Startposition für Infoblock
    info_y = 50  # Gleiche Höhe wie das Anschriftenfeld
    
    # Nur Datum im Infoblock (Ihr/Unser Zeichen entfernt)
    pdf.set_xy(info_x, info_y)
    pdf.set_font('Arial', '', 10)
    pdf.cell(25, 5, "Datum:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 5, f"{datetime.now().strftime('%d.%m.%Y')}", 0, 1)
    
    # Betreffzeile - exakt 8,4mm unterhalb des Anschriftenfeldes gemäß DIN 5008
    pdf.set_xy(25, 85)  # Genauer Abstand nach DIN 5008
    
    # Betreffzeile fett gedruckt (ohne das Wort "Betreff")
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 5, "Einladung zum 150 jährigen Feuerwehrfest", 0, 1, 'L')
    
    # Abstand nach der Betreffzeile - eine Leerzeile gemäß DIN 5008
    pdf.ln(6)
    
    # Haupttext mit Schriftgröße 11 (exakt nach DIN 5008 Empfehlung für Arial)
    pdf.set_font('Arial', '', 11)
    
    # Anrede mit Vereinsnamen
    pdf.multi_cell(0, 6, f"Hallo {invite.verein},", 0, 'L')
    pdf.ln(6)  # Eine Leerzeile nach DIN 5008
    
    # Einladungstext aus den Einstellungen
    if invite_header:
        # Trennung der Absätze durch Leerzeilen gemäß DIN 5008
        paragraphs = invite_header.split("\n\n")
        for i, paragraph in enumerate(paragraphs):
            # Ensure the text is safe for PDF generation
            try:
                # Try to encode to Latin-1 to catch any potential issues
                paragraph.encode('latin1')
                pdf.multi_cell(0, 6, paragraph, 0, 'L')
            except UnicodeEncodeError:
                # If encoding fails, replace problematic characters
                safe_paragraph = ''.join(c if ord(c) < 128 else ' ' for c in paragraph)
                pdf.multi_cell(0, 6, safe_paragraph, 0, 'L')
            
            if i < len(paragraphs) - 1:
                pdf.ln(6)  # Leerzeile zwischen Absätzen
    else:
        # Fallback, falls kein Text in den Einstellungen hinterlegt ist - mit korrekten Leerzeilen
        pdf.multi_cell(0, 6, f"Anlässlich unseres Festes laden wir herzlich nach {event_location or 'unseren Ort'} ein!", 0, 'L')
        pdf.ln(6)  # Leerzeile nach DIN 5008
        
        pdf.multi_cell(0, 6, f"Festumzug: {formatted_date or 'TBD'}, Aufstellung 13:00 Uhr, Start 13:30 Uhr.", 0, 'L')
        pdf.ln(6)  # Leerzeile nach DIN 5008
        
        pdf.multi_cell(0, 6, f"{vereins_name or 'Wir'} freuen uns auf Euer Kommen!", 0, 'L')
    
    # Abstand vor dem Anmeldebereich - gemäß DIN 5008 durch Absatzformatierung
    pdf.ln(10)
    
    # # Grußformel gemäß DIN 5008
    # pdf.multi_cell(0, 6, "Wir freuen uns auf euch und ein unvergessliches Fest!", 0, 'L')
    # pdf.ln(12)  # Platz für Unterschrift
    
    # # Name des Veranstalters/Unterzeichners
    # pdf.multi_cell(0, 6, f"{vereins_name or 'Festkomitee'}", 0, 'L')
    # pdf.ln(12)  # Abstand nach Unterschriftsbereich
    
    # Sichtbare Trennung - dünnere Linie nach DIN 5008
    pdf.set_draw_color(200, 200, 200)  # Hellgrau
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)  # Abstand nach Trennlinie
    
    # Überschrift für Anmeldung im Anlagebereich
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, 'Anmeldung:', 0, 1, 'L')
    pdf.ln(2)
    
    # QR-Code für die Anmeldung on-demand generieren
    from app.utils.qr_utils import generate_qr
    base_url = get_base_url()
    invite_url = f"{base_url}/respond/{invite.token}"
    
    # Generiere den QR-Code temporär
    logger.debug(f"Generating temporary QR code for PDF with URL: {invite_url}")
    temp_qr_path = generate_qr(invite_url, invite.verein, invite.token)
    
    if temp_qr_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)):
        qr_path = os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)
        qr_size = 45  # QR-Code-Größe erhöht für bessere Lesbarkeit
        # Direkt unter dem "A" von Anmeldung positionieren - noch weiter nach links verschoben
        pdf.image(qr_path, x=21, y=pdf.get_y(), w=qr_size, h=qr_size)
        
        # Text neben dem QR-Code
        pdf.set_font('Arial', '', 11)
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.set_xy(21 + qr_size + 5, pdf.get_y() + 5)
        logger.debug(f"Using base URL for PDF generation: {base_url}")
        pdf.multi_cell(page_width - qr_size - 5, 6, 
                      f"QR-Code scannen oder unter:\n{base_url}/respond/{invite.token}", 0, 'L')
    else:
        # Fallback ohne QR-Code
        pdf.set_font('Arial', '', 11)
        logger.debug(f"Using base URL for PDF generation (fallback): {base_url}")
        pdf.multi_cell(0, 6, f"Anmeldung unter: {base_url}/respond/{invite.token}", 0, 'L')
        qr_size = 0
    
    # Abstand nach dem QR-Code und Text
    pdf.ln(qr_size + 2 if qr_size > 0 else 10)
    
    # PDF speichern
    filename = f"Einladung_{invite.verein}_{invite.token}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    
    # Temporären QR-Code löschen, wenn er existiert
    if temp_qr_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)):
        try:
            os.remove(os.path.join(BASE_DIR, 'app', 'static', temp_qr_path))
            logger.debug(f"Deleted temporary QR code: {temp_qr_path}")
        except Exception as e:
            logger.error(f"Error deleting temporary QR code: {e}")
    
    return f"pdfs/{filename}"

def generate_all_invitations_pdf(invites, settings):
    """
    Generiert ein PDF mit allen Einladungen.
    
    Args:
        invites: Liste der Einladungs-Objekte
        settings: Dictionary mit Einstellungen für die Veranstaltung
    
    Returns:
        str: Pfad zur generierten PDF-Datei
    """
    # Stelle sicher, dass das PDF-Verzeichnis existiert
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Lösche alte PDF-Dateien, um Speicherplatz zu sparen
    cleanup_old_pdf_files()
    
    # Store settings in current_app.config to make them available to the footer method
    try:
        from flask import current_app
        # Update the CURRENT_SETTINGS with the passed settings
        current_app.config['CURRENT_SETTINGS'] = settings
    except:
        pass
    
    # PDF erstellen with settings
    pdf = InvitationPDF(settings=settings)
    
    for i, invite in enumerate(invites):
        pdf.add_page()
        
        # Inhalt für jede Einladung einzeln generieren
        # Die gleiche Logik wie in generate_invitation_pdf verwenden
        
        # 1. Absender (eigener Verein) - oben links
        vereins_name = settings.get("vereins_name", "")
        event_name = settings.get("event_name", "")
        event_date = settings.get("event_date", "")
        event_location = settings.get("event_location", "")
        event_time = settings.get("event_time", "")
        invite_header = settings.get("invite_header", "")
        
        # Dynamische Kontaktdaten aus den Einstellungen holen
        contact_address = settings.get("contact_address", "Musterstraße 123, 12345 Musterstadt")
        
        # Adresse für die Rücksendeadresse vorbereiten (nur Straße und Ort)
        address_parts = contact_address.split(',')
        short_address = address_parts[0] if len(address_parts) > 0 else contact_address
        
        # Nur die Rücksendeadresse (kleinere Schrift, im Briefkopf)
        # Wir entfernen den Briefkopf mit dem umrandeten Absender oben
        pdf.set_xy(25, 45)
        pdf.set_font('Arial', '', 7)
        pdf.cell(0, 3, f"{vereins_name} · {short_address} {address_parts[1].strip() if len(address_parts) > 1 else ''}", 0, 1, 'L')
        
        # Formatiere das Datum
        formatted_date = ""
        if event_date:
            try:
                date_obj = datetime.strptime(event_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                formatted_date = event_date
        
        # Anschriftenfeld - genau nach DIN 5008 (40 x 85 mm links)
        empfaenger_y = 50  # Startposition für den Empfänger (Anschriftenzone)
        
        # Empfänger (eingeladener Verein) - präzise DIN 5008-konforme Formatierung
        pdf.set_xy(25, empfaenger_y)
        pdf.set_font('Arial', '', 11)
        if invite.ansprechpartner:
            pdf.cell(0, 5, invite.ansprechpartner, 0, 1)
        pdf.cell(0, 5, invite.verein, 0, 1)
        if invite.strasse:
            pdf.cell(0, 5, invite.strasse, 0, 1)
        if invite.plz and invite.ort:
            pdf.cell(0, 5, f"{invite.plz} {invite.ort}", 0, 1)
        
        # Infoblock auf der rechten Seite - nur Datum gemäß DIN 5008
        info_x = pdf.w - 80  # Startposition für Infoblock
        info_y = 50  # Gleiche Höhe wie das Anschriftenfeld
        
        pdf.set_xy(info_x, info_y)
        pdf.set_font('Arial', '', 10)
        pdf.cell(25, 5, "Datum:", 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(30, 5, f"{datetime.now().strftime('%d.%m.%Y')}", 0, 1)
        
        # Betreffzeile - exakt 8,4mm unterhalb des Anschriftenfeldes gemäß DIN 5008
        pdf.set_xy(25, 85)  # Genauer Abstand nach DIN 5008
        
        # Betreffzeile fett gedruckt (ohne das Wort "Betreff")
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 5, "Einladung zum 150 jährigen Feuerwehrfest", 0, 1, 'L')
        # Abstand nach der Betreffzeile - eine Leerzeile gemäß DIN 5008
        pdf.ln(6)
        
        # Haupttext mit Schriftgröße 11 (exakt nach DIN 5008 Empfehlung für Arial)
        pdf.set_font('Arial', '', 11)
        
        # Anrede mit Vereinsnamen
        pdf.multi_cell(0, 6, f"Hallo {invite.verein},", 0, 'L')
        pdf.ln(6)  # Eine Leerzeile nach DIN 5008
        
        # Einladungstext aus den Einstellungen
        if invite_header:
            # Trennung der Absätze durch Leerzeilen gemäß DIN 5008
            paragraphs = invite_header.split("\n\n")
            for i, paragraph in enumerate(paragraphs):
                # Ensure the text is safe for PDF generation
                try:
                    # Try to encode to Latin-1 to catch any potential issues
                    paragraph.encode('latin1')
                    pdf.multi_cell(0, 6, paragraph, 0, 'L')
                except UnicodeEncodeError:
                    # If encoding fails, replace problematic characters
                    safe_paragraph = ''.join(c if ord(c) < 128 else ' ' for c in paragraph)
                    pdf.multi_cell(0, 6, safe_paragraph, 0, 'L')
                
                if i < len(paragraphs) - 1:
                    pdf.ln(6)  # Leerzeile zwischen Absätzen
        else:
            # Fallback, falls kein Text in den Einstellungen hinterlegt ist - mit korrekten Leerzeilen
            pdf.multi_cell(0, 6, f"Anlässlich unseres Festes laden wir herzlich nach {event_location or 'unseren Ort'} ein!", 0, 'L')
            pdf.ln(6)  # Leerzeile nach DIN 5008
            
            pdf.multi_cell(0, 6, f"Festumzug: {formatted_date or 'TBD'}, Aufstellung 13:00 Uhr, Start 13:30 Uhr.", 0, 'L')
            pdf.ln(6)  # Leerzeile nach DIN 5008
            
            pdf.multi_cell(0, 6, f"{vereins_name or 'Wir'} freuen uns auf Euer Kommen!", 0, 'L')
        
        # Abstand vor dem Anmeldebereich - gemäß DIN 5008 durch Absatzformatierung
        pdf.ln(10)
        
        # # Grußformel gemäß DIN 5008
        # pdf.multi_cell(0, 6, "Wir freuen uns auf euch und ein unvergessliches Fest!", 0, 'L')
        # pdf.ln(12)  # Platz für Unterschrift
        
        # # Name des Veranstalters/Unterzeichners
        # pdf.multi_cell(0, 6, f"{vereins_name or 'Festkomitee'}", 0, 'L')
        # pdf.ln(12)  # Abstand nach Unterschriftsbereich
        
        # Sichtbare Trennung - dünnere Linie nach DIN 5008
        pdf.set_draw_color(200, 200, 200)  # Hellgrau
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(6)  # Abstand nach Trennlinie
        
        # Überschrift für Anmeldung im Anlagebereich
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Anmeldung:', 0, 1, 'L')
        pdf.ln(2)
        
        # QR-Code für die Anmeldung on-demand generieren
        from app.utils.qr_utils import generate_qr
        base_url = get_base_url()
        invite_url = f"{base_url}/respond/{invite.token}"
        
        # Generiere den QR-Code temporär
        logger.debug(f"Generating temporary QR code for bulk PDF with URL: {invite_url}")
        temp_qr_path = generate_qr(invite_url, invite.verein, invite.token)
        
        # Track temporary QR files to delete them later
        if not hasattr(pdf, 'temp_qr_paths'):
            pdf.temp_qr_paths = []
        pdf.temp_qr_paths.append(temp_qr_path)
        
        if temp_qr_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)):
            qr_path = os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)
            qr_size = 45  # QR-Code-Größe erhöht für bessere Lesbarkeit
            # Direkt unter dem "A" von Anmeldung positionieren - noch weiter nach links verschoben
            pdf.image(qr_path, x=21, y=pdf.get_y(), w=qr_size, h=qr_size)
            
            # Text neben dem QR-Code
            pdf.set_font('Arial', '', 11)
            page_width = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.set_xy(21 + qr_size + 5, pdf.get_y() + 5)
            logger.debug(f"Using base URL for bulk PDF generation: {base_url}")
            pdf.multi_cell(page_width - qr_size - 5, 6, 
                        f"QR-Code scannen oder unter:\n{base_url}/respond/{invite.token}", 0, 'L')
        else:
            # Fallback ohne QR-Code
            pdf.set_font('Arial', '', 11)
            logger.debug(f"Using base URL for bulk PDF generation (fallback): {base_url}")
            pdf.multi_cell(0, 6, f"Anmeldung unter: {base_url}/respond/{invite.token}", 0, 'L')
            qr_size = 0
        
        # Abstand nach dem QR-Code und Text
        pdf.ln(qr_size + 2 if qr_size > 0 else 10)
    
    # PDF speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Alle_Einladungen_{timestamp}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    
    # Alle temporären QR-Codes löschen
    if hasattr(pdf, 'temp_qr_paths'):
        for temp_path in pdf.temp_qr_paths:
            if temp_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', temp_path)):
                try:
                    os.remove(os.path.join(BASE_DIR, 'app', 'static', temp_path))
                    logger.debug(f"Deleted temporary QR code: {temp_path}")
                except Exception as e:
                    logger.error(f"Error deleting temporary QR code: {e}")
    
    return f"pdfs/{filename}"
