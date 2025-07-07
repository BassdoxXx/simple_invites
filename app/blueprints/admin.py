from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import Response as FlaskResponse
from flask_login import login_required
from app.models import Invite, Response, Setting, db
from app.utils.qr_utils import generate_qr
import os
import csv
import io
import uuid
from datetime import datetime, timezone

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    Displays the admin dashboard with all invites and handles the creation or editing of invites.
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

    # Bearbeiten oder Erstellen einer Einladung
    invite_id = request.args.get("invite_id")
    invite = Invite.query.get(invite_id) if invite_id else None

    if request.method == "POST":
        verein = request.form.get("verein")
        tischnummer = request.form.get("tischnummer")
        token = request.form.get("token") or uuid.uuid4().hex[:10]  # Automatisch generieren, falls leer

        # Validierung: Prüfen, ob der Name des Gastes bereits existiert
        existing_name = Invite.query.filter(Invite.verein == verein, Invite.id != (invite.id if invite else None)).first()
        if existing_name:
            flash(f"Der Name '{verein}' wird bereits verwendet.", "danger")
            return redirect(url_for("admin.index", invite_id=invite_id))

        # Validierung: Prüfen, ob die Tischnummer bereits existiert
        if tischnummer:
            existing_tischnummer = Invite.query.filter(Invite.tischnummer == tischnummer, Invite.id != (invite.id if invite else None)).first()
            if existing_tischnummer:
                flash(f"Tischnummer {tischnummer} wird bereits verwendet.", "danger")
                return redirect(url_for("admin.index", invite_id=invite_id))

        # Wenn keine Tischnummer angegeben ist, finde die nächste freie Zahl
        if not tischnummer:
            # Alle bestehenden Tischnummern abrufen und sortieren
            existing_tischnummern = sorted(int(i.tischnummer) for i in invites if i.tischnummer.isdigit())
            
            if existing_tischnummern:
                # Suche die nächste freie Zahl
                for i in range(1, max(existing_tischnummern) + 2):
                    if i not in existing_tischnummern:
                        tischnummer = str(i)
                        break
            else:
                # Standardwert, falls keine Tischnummern existieren
                tischnummer = "1"

        if invite:
            # Bearbeiten einer bestehenden Einladung
            invite.verein = verein
            invite.tischnummer = tischnummer
            invite.token = token
        else:
            # Erstellen einer neuen Einladung
            link = url_for("public.respond", token=token, _external=True)
            qr_path = generate_qr(link, verein, token)
            invite = Invite(
                verein=verein,
                tischnummer=tischnummer,
                token=token,
                link=link,
                qr_code_path=qr_path,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(invite)

        db.session.commit()
        flash("Einladung erfolgreich gespeichert.", "success")
        return redirect(url_for("admin.index"))

    return render_template(
        "admin.html",
        invites=invites,
        responses=responses,
        whatsapp_active=whatsapp_active,
        response_count=response_count,
        total_invites=total_invites,
        total_persons=total_persons,
        invite=invite
    )

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
    Manages WhatsApp notification settings for the admin.

    Returns:
        - Redirect to the settings page after saving changes (POST request).
        - Rendered HTML template for the settings page (GET request).
    """
    phone_setting = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey_setting = Setting.query.filter_by(key="whatsapp_apikey").first()
    whatsapp_active = phone_setting and apikey_setting and phone_setting.value and apikey_setting.value
    invite_header_setting = Setting.query.filter_by(key="invite_header").first()
    if request.method == "POST":
        phone = request.form.get("phone")
        apikey = request.form.get("apikey")
        invite_header = request.form.get("invite_header")
        if phone_setting:
            phone_setting.value = phone
        else:
            db.session.add(Setting(key="whatsapp_phone", value=phone))
        if apikey_setting:
            apikey_setting.value = apikey
        else:
            db.session.add(Setting(key="whatsapp_apikey", value=apikey))
        if invite_header_setting:
            invite_header_setting.value = invite_header
        else:
            db.session.add(Setting(key="invite_header", value=invite_header))
            
        db.session.commit()
        flash("Einstellungen gespeichert", "success")
        return redirect(url_for("admin.settings"))
    
    return render_template(
        "admin_settings.html",
        phone=phone_setting.value if phone_setting else "",
        apikey=apikey_setting.value if apikey_setting else "",
        invite_header_value = invite_header_setting.value if invite_header_setting else "",
        whatsapp_active=whatsapp_active
    )
    
    
@admin_bp.route("/export/csv")
@login_required
def export_all_csv():
    invites = Invite.query.all()
    responses = {r.token: r for r in Response.query.all()}
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Verein", "Tischnummer", "Link", "Antwort", "Personen", "Getränke", "Zuletzt aktualisiert"])
    for invite in invites:
        res = responses.get(invite.token)
        full_link = url_for("public.respond", token=invite.token, _external=True)
        writer.writerow([
            invite.verein,
            invite.tischnummer,
            full_link,
            res.attending if res else "",
            res.persons if res else "",
            res.drinks if res else "",
            res.timestamp.strftime('%d.%m.%Y %H:%M') if res and res.timestamp else ""
        ])
    output.seek(0)
    return FlaskResponse(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=einladungen.csv"}
    )

@admin_bp.route("/export/csv/<token>")
@login_required
def export_single_csv(token):
    invite = Invite.query.filter_by(token=token).first_or_404()
    res = Response.query.filter_by(token=token).first()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Verein", "Tischnummer", "Link", "Antwort", "Personen", "Getränke", "Zuletzt aktualisiert"])
    full_link = url_for("public.respond", token=invite.token, _external=True)
    writer.writerow([
        invite.verein,
        invite.tischnummer,
        full_link,
        res.attending if res else "",
        res.persons if res else "",
        res.drinks if res else "",
        res.timestamp.strftime('%d.%m.%Y %H:%M') if res and res.timestamp else ""
    ])
    output.seek(0)
    return FlaskResponse(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=einladung_{invite.verein}_{invite.token}.csv"}
    )