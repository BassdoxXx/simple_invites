"""
Routes for PDF generation and QR code management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, current_app, request
from flask_login import login_required
from app.models import Invite, db
from app.utils.pdf_utils import generate_invitation_pdf, generate_all_invitations_pdf
from app.utils.qr_utils import generate_qr
from app.utils.settings_utils import get_multiple_settings, get_base_url
import os

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")

@pdf_bp.route("/", methods=["GET"])
@login_required
def index():
    """Show the PDF generation interface"""
    invites = Invite.query.order_by(Invite.verein).all()
    return render_template("generate_pdfs.html", invites=invites)

@pdf_bp.route("/generate/<token>", methods=["GET"])
@login_required
def generate_pdf(token):
    """Generate a PDF for a specific invitation"""
    invite = Invite.query.filter_by(token=token).first_or_404()
    
    # Get settings for the PDF
    settings = get_multiple_settings({
        "vereins_name": "",
        "event_name": "",
        "event_date": "",
        "event_location": "",
        "event_time": "",
        "invite_header": ""
    })
    
    # Generate the PDF
    pdf_path = generate_invitation_pdf(invite, settings)
    
    # Get only the filename from the path
    filename = os.path.basename(pdf_path)
    
    flash(f"PDF für {invite.verein} wurde erstellt.", "success")
    return redirect(url_for('static', filename=pdf_path))

@pdf_bp.route("/generate-selected-pdfs", methods=["POST"])
@login_required
def generate_selected_pdfs():
    """Generate PDFs for selected invitations based on form submission"""
    # Get selection type from form
    selection_type = request.form.get('selection_type')
    
    # Get settings for the PDF
    settings = get_multiple_settings({
        "vereins_name": "",
        "event_name": "",
        "event_date": "",
        "event_location": "",
        "event_time": "",
        "invite_header": ""
    })
    
    if selection_type == 'all':
        # Get all invites
        invites = Invite.query.order_by(Invite.verein).all()
        pdf_path = generate_all_invitations_pdf(invites, settings)
        flash(f"{len(invites)} Einladungen wurden in einer PDF-Datei zusammengefasst.", "success")
        return redirect(url_for('static', filename=pdf_path))
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
            flash(f"PDF für {invites[0].verein} wurde erstellt.", "success")
            return redirect(url_for('static', filename=pdf_path))
        # Ansonsten generiere eine PDF mit allen ausgewählten Einladungen
        else:
            pdf_path = generate_all_invitations_pdf(invites, settings)
            flash(f"{len(invites)} ausgewählte Einladungen wurden in einer PDF-Datei zusammengefasst.", "success")
            return redirect(url_for('static', filename=pdf_path))
    
    return redirect(url_for('static', filename=pdf_path))

@pdf_bp.route("/generate-all", methods=["GET"])
@login_required
def generate_all_pdfs():
    """Generate a PDF with all invitations"""
    invites = Invite.query.order_by(Invite.verein).all()
    
    # Get settings for the PDF
    settings = get_multiple_settings({
        "vereins_name": "",
        "event_name": "",
        "event_date": "",
        "event_location": "",
        "event_time": "",
        "invite_header": ""
    })
    
    # Generate the PDF
    pdf_path = generate_all_invitations_pdf(invites, settings)
    
    flash(f"{len(invites)} Einladungen wurden in einer PDF-Datei zusammengefasst.", "success")
    return redirect(url_for('static', filename=pdf_path))

