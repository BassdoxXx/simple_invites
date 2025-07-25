"""
Utilities for PDF invitation generation.
"""

import os
import glob
import time
from fpdf import FPDF
from datetime import datetime, timedelta
from flask import current_app

# Base directory of project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PDF_DIR = os.path.join(BASE_DIR, 'app', 'static', 'pdfs')
LOGO_PATH = os.path.join(BASE_DIR, 'app', 'static', 'images', 'logo.png')

# Stellen Sie sicher, dass das Verzeichnis existiert
os.makedirs(PDF_DIR, exist_ok=True)

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
                            print(f"Error deleting PDF file {pdf_file}: {e}")
            except Exception:
                # Fehler beim Lesen der Datei-Metadaten überspringen
                continue
                
        # Logge nur, wenn tatsächlich Dateien gelöscht wurden
        if deleted_count > 0:
            try:
                current_app.logger.info(f"PDF cleanup: deleted {deleted_count} files older than {max_age_minutes} minutes")
            except:
                print(f"PDF cleanup: deleted {deleted_count} files older than {max_age_minutes} minutes")
                
        # Logge Fehler nur, wenn welche aufgetreten sind
        if error_count > 0:
            try:
                current_app.logger.warning(f"PDF cleanup: encountered {error_count} errors while trying to delete files")
            except:
                print(f"PDF cleanup: encountered {error_count} errors while trying to delete files")
                
    except Exception as e:
        try:
            current_app.logger.error(f"Error during PDF cleanup: {e}")
        except:
            print(f"Error during PDF cleanup: {e}")

class InvitationPDF(FPDF):
    """Custom PDF class for invitation generation"""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        # DIN-A4 standard margins: 25mm (2.5cm) on all sides
        self.set_margins(25, 25, 25)
        self.set_auto_page_break(auto=True, margin=25)
        # Using standard fonts instead of custom fonts
        self.set_font('Arial', '', 10)  # Default font

    def header(self):
        # Add logo to the top right corner
        try:
            if os.path.exists(LOGO_PATH) and os.path.isfile(LOGO_PATH) and os.path.getsize(LOGO_PATH) > 0:
                # Get the width of the page
                page_width = self.w
                # Logo dimensions - adjust as needed
                logo_width = 40
                # Position logo in top right corner (respecting the margin)
                self.image(LOGO_PATH, x=page_width-65, y=10, w=logo_width)
        except Exception as e:
            # Log the error but continue without the logo
            print(f"Could not add logo: {e}")
        
        # Reset position for content
        self.ln(5)

    def footer(self):
        # Add website URL in the footer
        self.set_y(-20)  # 25mm from bottom plus some space
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)  # Black text
        self.cell(0, 10, "www.ffw-windischletten.de", 0, 0, 'C')

def generate_invitation_pdf(invite, settings):
    """
    Generiert ein PDF für eine Einladung basierend auf einem Layout-Template.
    
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
    
    # PDF erstellen
    pdf = InvitationPDF()
    pdf.add_page()
    
    # 1. Absender (eigener Verein) - oben links unter dem Briefkopf
    pdf.set_font('Arial', '', 8)
    pdf.cell(0, 5, vereins_name, 0, 1)
    pdf.cell(0, 5, f"Datum: {datetime.now().strftime('%d.%m.%Y')}", 0, 1)
    pdf.ln(15)
    
    # 2. Empfänger (eingeladener Verein) - links
    pdf.set_font('Arial', '', 11)
    if invite.ansprechpartner:
        pdf.cell(0, 5, invite.ansprechpartner, 0, 1)
    pdf.cell(0, 5, invite.verein, 0, 1)
    if invite.strasse:
        pdf.cell(0, 5, invite.strasse, 0, 1)
    if invite.plz and invite.ort:
        pdf.cell(0, 5, f"{invite.plz} {invite.ort}", 0, 1)
    pdf.ln(20)
    
    # 3. Überschrift "Einladung zum Jubiläum" mit Schriftgröße 20
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, "Einladung zum Jubiläum", 0, 1, 'C')
    pdf.ln(10)
    
    # 5. Haupttext mit Schriftgröße 12
    pdf.set_font('Arial', '', 12)
    
    # Fest definierter Text für die Einladung
    invite_text = """Sehr geehrte Feuerwehrkamerad*innen,

anlässlich unseres 150-jährigen Bestehens laden wir euch herzlich zum
Jubiläumsfest nach Windischletten ein!

Festumzug: Sonntag, 07.06.2026, Aufstellung 13:00 Uhr, Start 13:30 Uhr in Windischletten.

Danach: Lasst uns gemeinsam auf 150 Jahre anstoßen - Für beste Stimmung sorgen die Itzgrunder Musikanten! 

Jetzt anmelden: Einfach den QR-Code scannen oder uns auf anderem Weg Bescheid geben, mit wie
vielen Gästen ihr kommt."""
    
    # Text in mehreren Zeilen ausgeben
    pdf.multi_cell(0, 8, invite_text, 0, 'L')
    pdf.ln(10)
    
    # Veranstaltungsdetails sind bereits im Haupttext enthalten
    # Daher keine separate Auflistung mehr nötig
    
    pdf.ln(5)
    
    # 7. QR-Code einfügen zentral mit einer Kantenlänge von 2,6cm (26mm)
    
    # QR-Code Pfad ermitteln
    if invite.qr_code_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', invite.qr_code_path)):
        qr_path = os.path.join(BASE_DIR, 'app', 'static', invite.qr_code_path)
        # QR-Code zentriert einfügen
        pdf_width = pdf.w
        qr_width = 25  # QR-Code-Breite in mm (exakt 2,5cm wie gewünscht)
        # Zentriert innerhalb des verfügbaren Bereichs (unter Berücksichtigung der Ränder)
        pdf.image(qr_path, x=((pdf_width - 50) - qr_width)/2 + 25, y=pdf.get_y(), w=qr_width)
        pdf.ln(qr_width + 10)  # Platz nach dem QR-Code lassen
    else:
        # Wenn kein QR-Code verfügbar ist, Link anzeigen
        pdf.ln(5)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 5, "QR-Code nicht verfügbar. Bitte verwenden Sie folgenden Link:", 0, 1, 'C')
        pdf.ln(3)
        pdf.set_text_color(0, 0, 255)  # Blau für den Link
        pdf.cell(0, 5, invite.link, 0, 1, 'C', link=invite.link)
        pdf.set_text_color(0, 0, 0)  # Zurück zu schwarz
        pdf.ln(5)
            
    pdf.ln(5)
    
        
    # PDF speichern
    filename = f"Einladung_{invite.verein}_{invite.token}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    
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
    
    # PDF erstellen
    pdf = InvitationPDF()
    
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
        
        # Formatiere das Datum
        formatted_date = ""
        if event_date:
            try:
                date_obj = datetime.strptime(event_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                formatted_date = event_date
        
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, vereins_name, 0, 1)
        pdf.cell(0, 5, f"Datum: {datetime.now().strftime('%d.%m.%Y')}", 0, 1)
        pdf.ln(15)
        
        # 2. Empfänger (eingeladener Verein)
        pdf.set_font('Arial', '', 11)
        if invite.ansprechpartner:
            pdf.cell(0, 5, invite.ansprechpartner, 0, 1)
        pdf.cell(0, 5, invite.verein, 0, 1)
        if invite.strasse:
            pdf.cell(0, 5, invite.strasse, 0, 1)
        if invite.plz and invite.ort:
            pdf.cell(0, 5, f"{invite.plz} {invite.ort}", 0, 1)
        pdf.ln(20)
        
        # 3. Überschrift "Einladung zum Jubiläum" mit Schriftgröße 20
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 10, "Einladung zum Jubiläum", 0, 1, 'C')
        pdf.ln(10)
        
        # 5. Haupttext mit Schriftgröße 12
        pdf.set_font('Arial', '', 12)
        
        # Fest definierter Text für die Einladung
        invite_text = """Sehr geehrte Feuerwehrkamerad*innen,

anlässlich unseres 150-jährigen Bestehens laden wir euch herzlich zum
Jubiläumsfest nach Windischletten ein!

Festumzug: Sonntag, 07.06.2026, Aufstellung 13:00 Uhr, Start 13:30 Uhr in Windischletten.

Danach: Lasst uns gemeinsam auf 150 Jahre anstoßen - Für beste Stimmung sorgen die Itzgrunder Musikanten! 

Jetzt anmelden: Einfach den QR-Code scannen oder uns auf anderem Weg Bescheid geben, mit wie
vielen Gästen ihr kommt."""
        
        # Text in mehreren Zeilen ausgeben
        pdf.multi_cell(0, 8, invite_text, 0, 'L')
        pdf.ln(10)
        
        # Veranstaltungsdetails sind bereits im Haupttext enthalten
        # Daher keine separate Auflistung mehr nötig
        
        pdf.ln(5)
        
        # 7. QR-Code einfügen zentral mit einer Kantenlänge von 2,6cm (26mm)
        
        # QR-Code Pfad ermitteln
        if invite.qr_code_path and os.path.exists(os.path.join(BASE_DIR, 'app', 'static', invite.qr_code_path)):
            qr_path = os.path.join(BASE_DIR, 'app', 'static', invite.qr_code_path)
            # QR-Code zentriert einfügen
            pdf_width = pdf.w
            qr_width = 26  # QR-Code-Breite in mm (exakt 2,6cm wie gewünscht)
            # Zentriert innerhalb des verfügbaren Bereichs (unter Berücksichtigung der Ränder)
            pdf.image(qr_path, x=((pdf_width - 50) - qr_width)/2 + 25, y=pdf.get_y(), w=qr_width)
            pdf.ln(qr_width + 10)  # Platz nach dem QR-Code lassen
        else:
            # Wenn kein QR-Code verfügbar ist, Link anzeigen
            pdf.ln(5)
            pdf.set_font('Arial', '', 9)
            pdf.cell(0, 5, "QR-Code nicht verfügbar. Bitte verwenden Sie folgenden Link:", 0, 1, 'C')
            pdf.ln(3)
            pdf.set_text_color(0, 0, 255)  # Blau für den Link
            pdf.cell(0, 5, invite.link, 0, 1, 'C', link=invite.link)
            pdf.set_text_color(0, 0, 0)  # Zurück zu schwarz
            pdf.ln(5)
        
        pdf.ln(5)
        
        # 8. Abschluss
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, "Mit freundlichen Grüßen", 0, 1)
        pdf.ln(10)
        pdf.cell(0, 8, vereins_name, 0, 1)
    
    # PDF speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Alle_Einladungen_{timestamp}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    
    return f"pdfs/{filename}"
