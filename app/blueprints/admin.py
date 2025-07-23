from flask import Blueprint, render_template, request, redirect, url_for, flash, Response as FlaskResponse
from flask_login import login_required
from app.models import Invite, Response, Setting, TableAssignment, db
from app.utils.qr_utils import generate_qr
from app.utils.tisch_utils import assign_all_tables
import os
import csv
import io
import uuid
from datetime import datetime, timezone
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__)

def get_max_tables():
    max_tables_setting = Setting.query.filter_by(key="max_tables").first()
    return int(max_tables_setting.value) if max_tables_setting and max_tables_setting.value.isdigit() else 90

def get_blocked_tischnummern():
    invites = Invite.query.all()
    blocked = set(int(i.tischnummer) for i in invites if i.tischnummer and i.tischnummer.isdigit())
    blocked |= set(int(t.tischnummer) for t in TableAssignment.query.all() if str(t.tischnummer).isdigit())
    return blocked

def get_next_free_tischnummer(blocked, max_tables):
    for i in range(1, max_tables + 1):
        if i not in blocked:
            return str(i)
    return "1"

@admin_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    invites = Invite.query.all()
    responses = {r.token: r for r in Response.query.all()}
    max_tables = get_max_tables()

    if request.method == "POST":
        verein = request.form.get("verein")
        token = request.form.get("token") or uuid.uuid4().hex[:10]

        # Name-Validierung
        if Invite.query.filter(Invite.verein == verein).first():
            flash(f"Der Name '{verein}' wird bereits verwendet.", "danger")
            return redirect(url_for("admin.index"))

        # Automatische Tischnummer-Vergabe
        blocked = get_blocked_tischnummern()
        tischnummer = get_next_free_tischnummer(blocked, max_tables)

        # Einladung speichern
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
        assign_all_tables()
        flash("Einladung erfolgreich gespeichert.", "success")
        return redirect(url_for("admin.index"))

    # Statistiken und Anzeige
    response_count = len(responses)
    total_invites = len(invites)
    total_persons = sum(r.persons for r in responses.values() if r.attending == 'yes' and r.persons)
    phone = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey = Setting.query.filter_by(key="whatsapp_apikey").first()
    whatsapp_active = phone and apikey and phone.value and apikey.value

    enable_tables_setting = Setting.query.filter_by(key="enable_tables").first()
    max_tables_setting = Setting.query.filter_by(key="max_tables").first()
    enable_tables = enable_tables_setting.value if enable_tables_setting else "false"
    max_tables = max_tables_setting.value if max_tables_setting else "90"

    used_tables = len(set([ta.tischnummer for ta in TableAssignment.query.all()]))

    top_verein = "-"
    top_persons = 0
    if enable_tables == "true":
        top = db.session.query(TableAssignment.verein, func.sum(TableAssignment.personen))\
            .group_by(TableAssignment.verein)\
            .order_by(func.sum(TableAssignment.personen).desc())\
            .first()
        if top:
            top_verein = top[0]
            top_persons = top[1]

    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    table_assignments = TableAssignment.query.all()
    verein_tische = {}
    for ta in table_assignments:
        verein_tische.setdefault(ta.verein, []).append(str(ta.tischnummer))

    return render_template(
        "admin.html",
        invites=invites,
        responses=responses,
        whatsapp_active=whatsapp_active,
        response_count=response_count,
        total_invites=total_invites,
        total_persons=total_persons,
        vereins_name=vereins_name_setting.value if vereins_name_setting else "",
        enable_tables=enable_tables,
        max_tables=max_tables,
        used_tables=used_tables,
        top_verein=top_verein,
        top_persons=top_persons,
        verein_tische=verein_tische,
    )

@admin_bp.route("/delete/<token>", methods=["POST"])
@login_required
def delete_invite(token):
    invite = Invite.query.filter_by(token=token).first()
    response = Response.query.filter_by(token=token).first()
    if invite:
        TableAssignment.query.filter_by(verein=invite.verein).delete()
        db.session.commit()
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
    assign_all_tables()
    flash("Einladung gelöscht", "success")
    return redirect(url_for("admin.index"))

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    phone_setting = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey_setting = Setting.query.filter_by(key="whatsapp_apikey").first()
    invite_header_setting = Setting.query.filter_by(key="invite_header").first()
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    max_tables_setting = Setting.query.filter_by(key="max_tables").first()
    max_persons_setting = Setting.query.filter_by(key="max_persons_per_table").first()
    enable_tables_setting = Setting.query.filter_by(key="enable_tables").first()

    if request.method == "POST":
        phone = request.form.get("phone", "")
        apikey = request.form.get("apikey", "")
        invite_header = request.form.get("invite_header", "")
        event_name = request.form.get("event_name", "")
        vereins_name = request.form.get("vereins_name", "")
        max_tables = request.form.get("max_tables", "90")
        max_persons_per_table = request.form.get("max_persons_per_table", "10")
        enable_tables = request.form.get("enable_tables", "false")

        def save_setting(setting, key, value):
            if setting:
                setting.value = value
            else:
                db.session.add(Setting(key=key, value=value))

        save_setting(phone_setting, "whatsapp_phone", phone)
        save_setting(apikey_setting, "whatsapp_apikey", apikey)
        save_setting(invite_header_setting, "invite_header", invite_header)
        save_setting(event_name_setting, "event_name", event_name)
        save_setting(vereins_name_setting, "vereins_name", vereins_name)
        save_setting(max_tables_setting, "max_tables", max_tables)
        save_setting(max_persons_setting, "max_persons_per_table", max_persons_per_table)
        save_setting(enable_tables_setting, "enable_tables", enable_tables)

        db.session.commit()
        flash("Einstellungen gespeichert", "success")
        return redirect(url_for("admin.settings"))

    return render_template(
        "admin_settings.html",
        phone=phone_setting.value if phone_setting else "",
        apikey=apikey_setting.value if apikey_setting else "",
        invite_header=invite_header_setting.value if invite_header_setting else "",
        event_name=event_name_setting.value if event_name_setting else "",
        vereins_name=vereins_name_setting.value if vereins_name_setting else "",
        max_tables=max_tables_setting.value if max_tables_setting else "90",
        max_persons_per_table=max_persons_setting.value if max_persons_setting else "10",
        enable_tables=enable_tables_setting.value if enable_tables_setting else "false",
        whatsapp_active=(
            phone_setting and apikey_setting and phone_setting.value and apikey_setting.value
        )
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

@admin_bp.route("/edit/<token>", methods=["GET", "POST"])
@login_required
def edit_invite(token):
    invite = Invite.query.filter_by(token=token).first_or_404()
    max_tables = get_max_tables()

    if request.method == "POST":
        verein = request.form.get("verein")
        # tischnummer = request.form.get("tischnummer")  # Entfernen!
        token = request.form.get("token") or uuid.uuid4().hex[:10]

        # Name-Validierung
        if Invite.query.filter(Invite.verein == verein, Invite.id != invite.id).first():
            flash(f"Der Name '{verein}' wird bereits verwendet.", "danger")
            return redirect(url_for("admin.edit_invite", token=token))

        # Automatische Vergabe:
        blocked = get_blocked_tischnummern()
        blocked.discard(int(invite.tischnummer))  # Eigene Tischnummer beim Bearbeiten ignorieren
        tischnummer = get_next_free_tischnummer(blocked, max_tables)

        invite.verein = verein
        invite.tischnummer = tischnummer
        invite.manuell_gesetzt = bool(request.form.get("manuell_gesetzt"))
        db.session.commit()
        assign_all_tables()
        flash("Einladung erfolgreich bearbeitet.", "success")
        return redirect(url_for("admin.index"))

    return render_template(
        "edit_invite.html",
        invite=invite
    )