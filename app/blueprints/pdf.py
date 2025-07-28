"""
Routes for PDF generation and QR code management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, current_app, request
from flask_login import login_required
from app.models import Invite, db
from app.utils.pdf_utils import generate_invitation_pdf, generate_all_invitations_pdf, PDF_DIR
from app.utils.qr_utils import generate_qr
from app.utils.settings_utils import get_multiple_settings, get_base_url
import os
import re

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")

def sanitize_text_for_pdf(text):
    """
    Removes or replaces special characters that cause problems with the FPDF library
    
    Args:
        text: The text to be sanitized
    
    Returns:
        str: Sanitized text safe for PDF generation
    """
    if not text:
        return ""
    
    # Replace problematic characters with safer alternatives
    replacements = {
        '\u2013': '-',    # en dash
        '\u2014': '--',   # em dash
        '\u2018': "'",    # left single quote
        '\u2019': "'",    # right single quote
        '\u201C': '"',    # left double quote
        '\u201D': '"',    # right double quote
        '\u2022': '*',    # bullet
        '\u2026': '...',  # ellipsis
        '\u2039': '<',    # single left angle quote
        '\u203A': '>',    # single right angle quote
        '\u20AC': 'EUR',  # Euro symbol
        '\u2212': '-',    # minus sign
        '\u00A0': ' ',    # non-breaking space
        # Add more replacements as needed
    }
    
    # Apply the replacements
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Remove emoji and other special Unicode characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes
        "\U0001F800-\U0001F8FF"  # miscellaneous symbols
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub(" ", text)
    
    # Final safety check: convert any remaining non-Latin1 characters to spaces
    safe_text = ""
    for char in text:
        try:
            char.encode('latin1')
            safe_text += char
        except UnicodeEncodeError:
            safe_text += ' '
    
    return safe_text

@pdf_bp.route("/", methods=["GET"])
@login_required
def index():
    """Show the PDF generation interface"""
    invites = Invite.query.order_by(Invite.verein).all()
    return render_template("generate_pdfs.html", invites=invites)

@pdf_bp.route("/serve/<path:filename>", methods=["GET"])
@login_required
def serve_pdf(filename):
    """Serve a PDF file for download (cleanup happens via scheduled task)"""
    
    # Get the base filename
    base_filename = os.path.basename(filename)
    
    # Simply serve the file with proper headers - cleanup will be handled by the cleanup_old_pdf_files function
    return send_from_directory(PDF_DIR, base_filename, as_attachment=True)

@pdf_bp.route("/generate/<token>", methods=["GET"])
@login_required
def generate_pdf(token):
    """Generate a PDF for a specific invitation"""
    invite = Invite.query.filter_by(token=token).first_or_404()
    
    # Get settings for the PDF including contact information
    settings = get_multiple_settings({
        "vereins_name": "",
        "event_name": "",
        "event_date": "",
        "event_location": "",
        "event_time": "",
        "invite_header": "",
        "contact_email": "",
        "contact_address": "",
        "contact_phone": "",
        "website": ""
    })
    
    # Sanitize the invite_header to ensure it's safe for PDF generation
    if "invite_header" in settings and settings["invite_header"]:
        settings["invite_header"] = sanitize_text_for_pdf(settings["invite_header"])
    
    # Generate the PDF
    pdf_path = generate_invitation_pdf(invite, settings)
    
    # Get only the filename from the path
    filename = os.path.basename(pdf_path)
    
    # Only show flash messages to admin users
    if request.referrer and '/admin/' in request.referrer:
        flash(f"PDF für {invite.verein} wurde erstellt.", "success")
    
    # Serve the file directly
    return redirect(url_for('pdf.serve_pdf', filename=filename))

@pdf_bp.route("/generate-selected-pdfs", methods=["POST"])
@login_required
def generate_selected_pdfs():
    """Generate PDFs for selected invitations based on form submission"""
    # Get selection type from form
    selection_type = request.form.get('selection_type')
    
    # Get settings for the PDF including contact information
    settings = get_multiple_settings({
        "vereins_name": "",
        "event_name": "",
        "event_date": "",
        "event_location": "",
        "event_time": "",
        "invite_header": "",
        "contact_email": "",
        "contact_address": "",
        "contact_phone": "",
        "website": ""
    })
    
    # Sanitize the invite_header to ensure it's safe for PDF generation
    if "invite_header" in settings and settings["invite_header"]:
        settings["invite_header"] = sanitize_text_for_pdf(settings["invite_header"])
    
    if selection_type == 'all':
        # Get all invites
        invites = Invite.query.order_by(Invite.verein).all()
        pdf_path = generate_all_invitations_pdf(invites, settings)
        filename = os.path.basename(pdf_path)
        
        # Show flash message and start download
        flash(f"{len(invites)} Einladungen wurden in einer PDF-Datei zusammengefasst.", "success")
        return redirect(url_for('pdf.serve_pdf', filename=filename))
    else:
        # Get selected invite tokens
        selected_tokens = request.form.getlist('selected_invites')
        
        if not selected_tokens:
            flash("Bitte wählen Sie mindestens eine Einladung aus.", "warning")
            return redirect(url_for('admin.index'))
        
        # Get the selected invites
        invites = Invite.query.filter(Invite.token.in_(selected_tokens)).order_by(Invite.verein).all()
        
        # Wenn nur ein Eintrag ausgewählt wurde, generiere eine einzelne PDF
        if len(invites) == 1:
            pdf_path = generate_invitation_pdf(invites[0], settings)
            filename = os.path.basename(pdf_path)
            
            # Show flash message and start download
            flash(f"PDF für {invites[0].verein} wurde erstellt.", "success")
            return redirect(url_for('pdf.serve_pdf', filename=filename))
        # Ansonsten generiere eine PDF mit allen ausgewählten Einladungen
        else:
            pdf_path = generate_all_invitations_pdf(invites, settings)
            filename = os.path.basename(pdf_path)
            
            # Show flash message and start download
            flash(f"{len(invites)} ausgewählte Einladungen wurden in einer PDF-Datei zusammengefasst.", "success")
            return redirect(url_for('pdf.serve_pdf', filename=filename))
    
    # This line should never be reached, as all paths above return
    return redirect(url_for('admin.index'))

@pdf_bp.route("/generate-all", methods=["GET"])
@login_required
def generate_all_pdfs():
    """Generate a PDF with all invitations"""
    invites = Invite.query.order_by(Invite.verein).all()
    
    # Get settings for the PDF including contact information
    settings = get_multiple_settings({
        "vereins_name": "",
        "event_name": "",
        "event_date": "",
        "event_location": "",
        "event_time": "",
        "invite_header": "",
        "contact_email": "",
        "contact_address": "",
        "contact_phone": "",
        "website": ""
    })
    
    # Sanitize the invite_header to ensure it's safe for PDF generation
    if "invite_header" in settings and settings["invite_header"]:
        settings["invite_header"] = sanitize_text_for_pdf(settings["invite_header"])
    
    # Generate the PDF
    pdf_path = generate_all_invitations_pdf(invites, settings)
    filename = os.path.basename(pdf_path)
    
    # Only show flash messages for admin users
    if request.referrer and '/admin/' in request.referrer:
        flash(f"{len(invites)} Einladungen wurden in einer PDF-Datei zusammengefasst.", "success")
        
    return redirect(url_for('pdf.serve_pdf', filename=filename))

