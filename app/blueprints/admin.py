from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Invite, Response, Setting, db
from app.utils.qr_utils import generate_qr
import os
import uuid
from datetime import datetime, timezone

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
@login_required
def index():
    """
    Displays the admin dashboard with all invites, responses, and statistics.

    Returns:
        Rendered HTML template for the admin dashboard.
    """
    invites = Invite.query.all()
    responses = {r.token: r for r in Response.query.all()}
    response_count = len(responses)
    total_invites = len(invites)
    total_persons = sum(
        r.persons for r in responses.values()
        if r.attending == 'yes' and r.persons
    )
    phone = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey = Setting.query.filter_by(key="whatsapp_apikey").first()
    whatsapp_active = phone and apikey and phone.value and apikey.value
    return render_template(
        "admin.html",
        invites=invites,
        responses=responses,
        whatsapp_active=whatsapp_active,
        response_count=response_count,
        total_invites=total_invites,
        total_persons=total_persons
    )

@admin_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_invite():
    """
    Handles the creation of a new invite and generates a QR code for it.

    Returns:
        - Redirect to the admin dashboard if the invite is successfully created.
        - Rendered HTML template for the invite creation form if the request method is GET.
    """
    if request.method == "POST":
        verein = request.form.get("verein")
        adresse = request.form.get("adresse")
        token = adresse.strip() if adresse else uuid.uuid4().hex[:10]
        link = f"/respond/{token}"
        qr_path = generate_qr(link, token)
        invite = Invite(
            verein=verein,
            adresse="",
            token=token,
            link=link,
            qr_code_path=qr_path,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(invite)
        db.session.commit()
        flash("Einladung erstellt", "success")
        return redirect(url_for("admin.index"))
    return render_template("invite_form.html")

@admin_bp.route("/delete/<token>", methods=["POST"])
@login_required
def delete_invite(token):
    """
    Deletes an invite and its associated QR code and response, if any.

    Args:
        token (str): The unique token of the invite to be deleted.

    Returns:
        Redirect to the admin dashboard after the invite is deleted.
    """
    invite = Invite.query.filter_by(token=token).first()
    response = Response.query.filter_by(token=token).first()
    if invite:
        try:
            qr_path = os.path.join("app", "static", invite.qr_code_path)
            if os.path.exists(qr_path):
                os.remove(qr_path)
        except Exception as e:
            print(f"⚠️ QR-Code konnte nicht gelöscht werden: {e}")
        db.session.delete(invite)
    if response:
        db.session.delete(response)
    db.session.commit()
    flash("Einladung gelöscht", "success")
    return redirect(url_for("admin.index"))

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Manages WhatsApp notification settings and the invite header for the admin.

    Returns:
        - Redirect to the settings page after saving changes (POST request).
        - Rendered HTML template for the settings page (GET request).
    """
    phone_setting = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey_setting = Setting.query.filter_by(key="whatsapp_apikey").first()
    invite_header_setting = Setting.query.filter_by(key="invite_header").first()

    if request.method == "POST":
        # Eingaben aus dem Formular abrufen
        phone = request.form.get("phone", "").strip()
        apikey = request.form.get("apikey", "").strip()
        invite_header = request.form.get("invite_header", "").strip()

        # Validierung: Nur speichern, wenn ein Wert vorhanden ist
        if phone_setting:
            phone_setting.value = phone if phone else phone_setting.value
        elif phone:
            db.session.add(Setting(key="whatsapp_phone", value=phone))

        if apikey_setting:
            apikey_setting.value = apikey if apikey else apikey_setting.value
        elif apikey:
            db.session.add(Setting(key="whatsapp_apikey", value=apikey))

        if invite_header_setting:
            invite_header_setting.value = invite_header if invite_header else invite_header_setting.value
        elif invite_header:
            db.session.add(Setting(key="invite_header", value=invite_header))

        # Änderungen speichern
        db.session.commit()
        flash("Einstellungen gespeichert", "success")
        return redirect(url_for("admin.settings"))

    # Werte für das Template abrufen
    return render_template(
        "admin_settings.html",
        phone=phone_setting.value if phone_setting else "",
        apikey=apikey_setting.value if apikey_setting else "",
        invite_header_value=invite_header_setting.value if invite_header_setting else "",
    )