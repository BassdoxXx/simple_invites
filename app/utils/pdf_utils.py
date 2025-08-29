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

def add_fold_marks(pdf):
    """
    Fügt DIN 5008 Falzmarken zum PDF hinzu.
    """
    # Save current line width setting
    line_width = pdf.line_width
    
    # Set thin light gray line for folding marks
    pdf.set_line_width(0.1)
    pdf.set_draw_color(200, 200, 200)
    
    # First fold mark at 105mm from top (for DIN lang envelope)
    pdf.line(5, 105, 8, 105)
    
    # Second fold mark at 210mm from top (for folding in thirds)
    pdf.line(5, 210, 8, 210)
    
    # Restore original settings
    pdf.set_line_width(line_width)
    pdf.set_draw_color(0)

def add_invitation_content(pdf, invite, settings):
    """
    Fügt den Inhalt einer Einladung zum PDF hinzu.
    
    Args:
        pdf: Das PDF-Objekt
        invite: Das Einladungs-Objekt
        settings: Dictionary mit Einstellungen
    """
    # Falzmarken hinzufügen
    add_fold_marks(pdf)
    
    # Vorbereitung: Veranstaltungsinformationen aus den Settings extrahieren
    vereins_name = settings.get("vereins_name", "")
    invite_header = settings.get("invite_header", "")
    contact_address = settings.get("contact_address", "Musterstraße 123, 12345 Musterstadt")
    
    # Adresse für die Rücksendeadresse vorbereiten (nur Straße und Ort)
    address_parts = contact_address.split(',')
    short_address = address_parts[0] if len(address_parts) > 0 else contact_address
    
    # Rücksendeadresse (kleinere Schrift, im Briefkopf)
    pdf.set_xy(25, 45)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 3, f"{vereins_name} · {short_address} · {address_parts[1].strip() if len(address_parts) > 1 else ''}", 0, 1, 'L')
    
    # Anschriftenfeld - genau nach DIN 5008
    empfaenger_y = 50
    pdf.set_xy(25, empfaenger_y)
    pdf.set_font('Arial', '', 11)
    if invite.ansprechpartner:
        pdf.cell(0, 5, invite.ansprechpartner, 0, 1)
    pdf.cell(0, 5, invite.verein, 0, 1)
    if invite.strasse:
        pdf.cell(0, 5, invite.strasse, 0, 1)
    if invite.plz and invite.ort:
        pdf.cell(0, 5, f"{invite.plz} {invite.ort}", 0, 1)
    
    # Datum im Infoblock
    info_x = pdf.w - 80
    info_y = 50
    pdf.set_xy(info_x, info_y)
    pdf.set_font('Arial', '', 10)
    pdf.cell(25, 5, "Datum:", 0, 0)
    pdf.cell(30, 5, f"{datetime.now().strftime('%d.%m.%Y')}", 0, 1)
    
    # Betreffzeile
    pdf.set_xy(25, 85)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 5, "Einladung zum 150 jährigen Feuerwehrfest", 0, 1, 'L')
    pdf.ln(6)
    
    # FESTE POSITION FÜR QR-CODE-BEREICH
    QR_SECTION_Y = 215
    
    # Haupttext
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, f"Hallo {invite.verein},", 0, 'L')
    pdf.ln(6)
    
    # Einladungstext aus den Einstellungen (nur wenn vorhanden)
    if invite_header:
        paragraphs = invite_header.split("\n\n")
        for i, paragraph in enumerate(paragraphs):
            if pdf.get_y() > QR_SECTION_Y - 20:
                break
                
            try:
                paragraph.encode('latin1')
                pdf.multi_cell(0, 6, paragraph, 0, 'L')
            except UnicodeEncodeError:
                safe_paragraph = ''.join(c if ord(c) < 128 else ' ' for c in paragraph)
                pdf.multi_cell(0, 6, safe_paragraph, 0, 'L')
            
            if i < len(paragraphs) - 1 and pdf.get_y() < QR_SECTION_Y - 20:
                pdf.ln(6)
    
    # FESTE POSITION FÜR QR-CODE-BEREICH
    pdf.set_y(QR_SECTION_Y)
    
    # Trennung
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)
    
    # QR-Code-Bereich
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, 'Anmeldung:', 0, 1, 'L')
    pdf.ln(2)
    
    # QR-Code generieren und einfügen
    from app.utils.qr_utils import generate_qr
    base_url = get_base_url()
    invite_url = f"{base_url}/respond/{invite.token}"
    
    temp_qr_path = generate_qr(invite_url, invite.verein, invite.token)
    
    if temp_qr_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)):
        qr_path = os.path.join(BASE_DIR, 'app', 'static', temp_qr_path)
        qr_size = 45
        pdf.image(qr_path, x=21, y=pdf.get_y(), w=qr_size, h=qr_size)
        
        pdf.set_font('Arial', '', 11)
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.set_xy(21 + qr_size + 5, pdf.get_y() + 5)
        pdf.multi_cell(page_width - qr_size - 5, 6, 
                      f"QR-Code scannen oder unter:\n{base_url}/respond/{invite.token}", 0, 'L')
        
        # Temporären QR-Code löschen
        try:
            os.remove(os.path.join(BASE_DIR, 'app', 'static', temp_qr_path))
        except Exception as e:
            logger.error(f"Error deleting temporary QR code: {e}")
    else:
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 6, f"Anmeldung unter: {base_url}/respond/{invite.token}", 0, 'L')

def generate_invitation_pdf(invite, settings):
    """
    Generiert ein PDF für eine Einladung basierend auf einem Layout-Template.
    Erzeugt dafür temporär einen QR-Code, der nach der PDF-Erstellung wieder gelöscht wird.
    """
    # Prüfen, ob die notwendigen Attribute vorhanden sind
    if not invite or not invite.verein:
        return None
    
    # Stelle sicher, dass das PDF-Verzeichnis existiert
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Lösche alte PDF-Dateien, um Speicherplatz zu sparen
    cleanup_old_pdf_files()
    
    # Store settings in current_app.config to make them available to the footer method
    try:
        from flask import current_app
        current_app.config['CURRENT_SETTINGS'] = settings
    except:
        pass
    
    # PDF erstellen mit DIN-A4-Format
    pdf = InvitationPDF(settings=settings)
    pdf.add_page()
    
    # Brief-Inhalt hinzufügen
    add_invitation_content(pdf, invite, settings)
    
    # PDF speichern
    filename = f"Einladung_{invite.verein}_{invite.token}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    
    return f"pdfs/{filename}"

def generate_all_invitations_pdf(invites, settings):
    """
    Generiert ein PDF mit allen Einladungen.
    """
    # Stelle sicher, dass das PDF-Verzeichnis existiert
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Lösche alte PDF-Dateien, um Speicherplatz zu sparen
    cleanup_old_pdf_files()
    
    # Store settings in current_app.config to make them available to the footer method
    try:
        from flask import current_app
        current_app.config['CURRENT_SETTINGS'] = settings
    except:
        pass
    
    # PDF erstellen mit DIN-A4-Format
    pdf = InvitationPDF(settings=settings)
    
    for invite in invites:
        pdf.add_page()
        add_invitation_content(pdf, invite, settings)
    
    # PDF speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Alle_Einladungen_{timestamp}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    
    return f"pdfs/{filename}"
