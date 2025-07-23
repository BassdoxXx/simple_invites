from flask import Blueprint, render_template, request, redirect, url_for, flash, Response as FlaskResponse
from flask_login import login_required
from app.models import Invite, Response, Setting, TableAssignment, db
from app.utils.qr_utils import generate_qr as generate_qr_code  # Korrekter Import
from app.utils.tisch_utils import assign_all_tables
import os
import csv
import io
import uuid
import random
import string
from datetime import datetime, timezone
from sqlalchemy import func
from functools import lru_cache

admin_bp = Blueprint("admin", __name__)

# Cache settings for 60 seconds to reduce DB queries
# Why: Settings rarely change but are accessed frequently
@lru_cache(maxsize=32)
def get_setting(key, default=None, expire_after=60):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default

def get_multiple_settings(setting_definitions):
    """Get multiple settings at once, using cached values.
    
    Why: Reduces code duplication when multiple settings are needed
    in a single context, while still benefiting from caching.
    
    Args:
        setting_definitions: Dict mapping setting keys to their default values
        
    Returns:
        Dict containing all requested settings with their values
    """
    return {key: get_setting(key, default) for key, default in setting_definitions.items()}

def get_max_tables():
    """Get maximum number of tables from settings.
    
    Why: This is a frequently accessed value that impacts table assignments
    and validations throughout the application.
    """
    max_tables_setting = get_setting("max_tables", "90")
    return int(max_tables_setting) if max_tables_setting.isdigit() else 90

def get_blocked_tischnummern():
    """Get all currently occupied table numbers.
    
    Why: We need to track all assigned table numbers to prevent duplicates,
    both from manual assignments and automatic distribution.
    """
    invites = Invite.query.all()
    # First collect manually assigned tables from invites
    blocked = set(int(i.tischnummer) for i in invites if i.tischnummer and i.tischnummer.isdigit())
    # Then add tables from automatic assignments
    blocked |= set(int(t.tischnummer) for t in TableAssignment.query.all() if str(t.tischnummer).isdigit())
    return blocked

def get_next_free_tischnummer(blocked, max_tables):
    """Find the next available table number.
    
    Why: When creating new invites or resetting table assignments,
    we need to find the lowest available table number to ensure efficient
    use of available tables.
    """
    for i in range(1, max_tables + 1):
        if i not in blocked:
            return str(i)
    return "1"  # Fallback if all tables are taken

def build_verein_tische_map():
    """Create a mapping of associations to their assigned tables.
    
    Why: This centralized function creates a consistent representation of
    table assignments that's used in multiple templates.
    """
    table_assignments = TableAssignment.query.all()
    verein_tische = {}
    for ta in table_assignments:
        verein_tische.setdefault(ta.verein, []).append(str(ta.tischnummer))
    return verein_tische

# Bestehende Index-Route ohne Formularverarbeitung
@admin_bp.route("/", methods=["GET"])
@login_required
def index():
    """Admin dashboard for managing invitations."""
    invites = Invite.query.all()
    responses = {r.token: r for r in Response.query.all()}
    max_tables = get_max_tables()

    # Prepare statistics and data for the template
    settings = get_multiple_settings({
        "enable_tables": "false",
        "max_tables": "90",
        "vereins_name": ""
    })
    
    enable_tables = settings["enable_tables"]
    max_tables_value = settings["max_tables"]
    
    # Calculate statistics
    response_count = Response.query.filter_by(attending='yes').count()
    total_invites = len(invites)
    total_persons = sum(r.persons for r in responses.values() if r.attending == 'yes' and r.persons)
    
    # Table statistics 
    used_tables = 0
    top_verein = "-"
    top_persons = 0
    verein_tische = {}
    
    if enable_tables == "true":
        used_tables = len(set([ta.tischnummer for ta in TableAssignment.query.all()]))
        verein_tische = build_verein_tische_map()
        
        # Find association with most guests
        top = db.session.query(
            TableAssignment.verein, 
            func.sum(TableAssignment.personen)
        ).group_by(TableAssignment.verein).order_by(
            func.sum(TableAssignment.personen).desc()
        ).first()
        
        if top:
            top_verein = top[0]
            top_persons = top[1]

    # Tischzuweisungen für detaillierte Ansicht
    table_assignments = TableAssignment.query.all()
    tisch_belegung = {}
    max_persons_per_table = int(get_setting("max_persons_per_table", "10"))

    for ta in table_assignments:
        tisch_nr = str(ta.tischnummer)
        if tisch_nr not in tisch_belegung:
            tisch_belegung[tisch_nr] = {"belegt": 0, "vereine": []}
        
        tisch_belegung[tisch_nr]["vereine"].append((ta.verein, ta.personen))
        tisch_belegung[tisch_nr]["belegt"] += ta.personen

    # Sortiere die Tische nach Nummer
    tisch_belegung = dict(sorted(tisch_belegung.items(), key=lambda item: int(item[0])))

    return render_template(
        "admin.html",
        invites=invites,
        responses=responses,
        response_count=response_count,
        total_invites=total_invites,
        total_persons=total_persons,
        vereins_name=settings["vereins_name"],
        enable_tables=enable_tables,
        max_tables=max_tables,  # ist jetzt ein int!
        used_tables=used_tables,  # ebenfalls int
        top_verein=top_verein,
        top_persons=top_persons,
        verein_tische=verein_tische,
        tisch_belegung=tisch_belegung,
        max_persons_per_table=max_persons_per_table
    )

# Neue Route für die Einladungserstellung
@admin_bp.route("/create-invite", methods=["GET", "POST"])
@login_required
def create_invite():
    """Create or edit an invitation."""
    invite_id = request.args.get("invite_id")
    invite = None
    
    if invite_id:
        invite = Invite.query.get(invite_id)
        if not invite:
            flash("Einladung nicht gefunden.", "danger")
            return redirect(url_for("admin.index"))
    
    if request.method == "POST":
        verein = request.form.get("verein", "").strip()
        
        # Entweder Token vom Formular nehmen oder einen 8-stelligen generieren
        form_token = request.form.get("token", "").strip()
        if form_token and len(form_token) == 8:
            token = form_token
        else:
            # Generiere einen 8-stelligen alphanumerischen Token (kleinbuchstaben und Zahlen)
            token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            
            # Stelle sicher, dass der Token einzigartig ist
            while Invite.query.filter_by(token=token).first():
                token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        if invite:
            # Bestehende Einladung aktualisieren
            invite.verein = verein
            if form_token:  # Nur aktualisieren, wenn explizit ein neuer Token eingegeben wurde
                invite.token = token
                
            db.session.commit()
            
            # QR-Code neu generieren, falls sich der Verein oder Token geändert hat
            qr_file_name = f"qr_{invite.token}.png"
            qr_path = os.path.join("app", "static", "qr_codes", qr_file_name)
            
            base_url = get_setting("base_url", "http://localhost:5000")
            invite_url = f"{base_url}/respond/{invite.token}"
            generate_qr_code(invite_url, qr_path)
            
            flash(f"Einladung für {verein} wurde aktualisiert.", "success")
        else:
            # Neue Einladung erstellen
            new_invite = Invite(verein=verein, token=token)
            db.session.add(new_invite)
            db.session.commit()
            
            # QR-Code generieren
            qr_file_name = f"qr_{token}.png"
            qr_path = os.path.join("app", "static", "qr_codes", qr_file_name)
            
            base_url = get_setting("base_url", "http://localhost:5000")
            invite_url = f"{base_url}/respond/{token}"
            generate_qr_code(invite_url, qr_path)
            
            flash(f"Neue Einladung für {verein} wurde erstellt.", "success")
        
        return redirect(url_for("admin.index"))
    
    # Lade den Vereinsnamen für die Anzeige
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    vereins_name = vereins_name_setting.value if vereins_name_setting else ""
    
    return render_template(
        "admin_create_invite.html", 
        invite=invite,
        vereins_name=vereins_name
    )

@admin_bp.route("/delete/<token>", methods=["POST"])
@login_required
def delete_invite(token):
    """Delete an invitation and its associated data.
    
    Why: Provides a way to remove invitations that were created by mistake
    or are no longer needed, cleaning up all related data.
    """
    invite = Invite.query.filter_by(token=token).first()
    response = Response.query.filter_by(token=token).first()
    
    if invite:
        # First remove any table assignments
        TableAssignment.query.filter_by(verein=invite.verein).delete()
        db.session.commit()
        
        # Then try to remove the QR code file
        try:
            qr_path = os.path.join("app", "static", invite.qr_code_path)
            if os.path.exists(qr_path):
                os.remove(qr_path)
        except Exception as e:
            print(f"⚠️ QR-Code konnte nicht gelöscht werden: {e}")
        
        # Finally remove the invitation
        db.session.delete(invite)
    
    # Remove response if exists
    if response:
        db.session.delete(response)
    
    db.session.commit()
    
    # Recalculate table assignments after deletion
    assign_all_tables()
    
    flash("Einladung gelöscht", "success")
    return redirect(url_for("admin.index"))

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Manage application settings."""
    # Define all settings with their keys and default values
    setting_definitions = {
        "invite_header": "",
        "event_name": "",
        "vereins_name": "",
        "max_tables": "90",
        "max_persons_per_table": "10",
        "enable_tables": "false"
    }
    
    if request.method == "POST":
        # Process all settings from the form
        for key in setting_definitions:
            value = request.form.get(key, setting_definitions[key])
            setting = Setting.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
            else:
                db.session.add(Setting(key=key, value=value))
        
        db.session.commit()
        
        # Clear setting cache to ensure latest values are used
        get_setting.cache_clear()
        
        flash("Einstellungen gespeichert", "success")
        return redirect(url_for("admin.settings"))

    # Optimiert: Alle Einstellungen auf einmal abrufen
    current_settings = get_multiple_settings(setting_definitions)
    
    return render_template(
        "admin_settings.html",
        **current_settings,
    )

@admin_bp.route("/export/csv")
@login_required
def export_all_csv():
    """Export all invitations and responses to a CSV file."""
    invites = Invite.query.all()
    responses = {r.token: r for r in Response.query.all()}
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Entferne "Getränke" aus den Headerzeilen
    writer.writerow([
        "Verein", "Tischnummer", "Link", "Antwort", 
        "Personen", "Zuletzt aktualisiert"
    ])
    
    for invite in invites:
        res = responses.get(invite.token)
        full_link = url_for("public.respond", token=invite.token, _external=True)
        
        writer.writerow([
            invite.verein,
            invite.tischnummer,
            full_link,
            res.attending if res else "",
            res.persons if res else "",
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
    """Export a single invitation with its response to CSV.
    
    Why: Allows exporting details about specific invitations for focused
    record keeping or communication purposes.
    """
    invite = Invite.query.filter_by(token=token).first_or_404()
    res = Response.query.filter_by(token=token).first()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow([
        "Verein", "Tischnummer", "Link", "Antwort", 
        "Personen", "Zuletzt aktualisiert"  # "Getränke" entfernen
    ])
    
    full_link = url_for("public.respond", token=invite.token, _external=True)
    writer.writerow([
        invite.verein,
        invite.tischnummer,
        full_link,
        res.attending if res else "",
        res.persons if res else "",
        res.timestamp.strftime('%d.%m.%Y %H:%M') if res and res.timestamp else ""
    ])
    
    output.seek(0)
    return FlaskResponse(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=einladung_{invite.verein}_{invite.token}.csv"}
    )

# Die neue edit_invite Route sollte so lauten:
@admin_bp.route("/edit/<token>", methods=["GET", "POST"])
@login_required
def edit_invite(token):
    """Edit an existing invitation by redirecting to create_invite."""
    invite = Invite.query.filter_by(token=token).first_or_404()
    return redirect(url_for("admin.create_invite", invite_id=invite.id))

@admin_bp.route("/assign_table/<token>", methods=["GET", "POST"])
@login_required
def assign_table(token):
    """Manually assign a table to an invitation."""
    invite = Invite.query.filter_by(token=token).first_or_404()
    
    # Holen der relevanten Tischdaten und Einstellungen
    max_tables = int(get_setting("max_tables", "90"))
    max_persons_per_table = int(get_setting("max_persons_per_table", "10"))
    
    # Zugehörige Response für Personenzahl
    response = Response.query.filter_by(token=token).first()
    
    if request.method == "POST":
        tisch_nr = request.form.get("tischnummer", "").strip()
        
        if tisch_nr and tisch_nr.isdigit():
            # Wenn eine Tischnummer eingegeben wurde, als manuell gesetzt markieren
            invite.tischnummer = tisch_nr
            invite.manuell_gesetzt = True
            db.session.commit()
            
            # Tische neu berechnen
            assign_all_tables()
            
            flash(f"Tisch {tisch_nr} wurde für {invite.verein} zugewiesen.", "success")
        else:
            # Falls keine Tischnummer eingegeben wurde, zur automatischen Zuweisung zurückkehren
            invite.tischnummer = None
            invite.manuell_gesetzt = False
            db.session.commit()
            
            # Tische neu berechnen
            assign_all_tables()
            
            flash(f"Tischzuweisung für {invite.verein} wird nun automatisch berechnet.", "success")
            
        return redirect(url_for("admin.index"))
    
    # Liste der bereits belegten Tische
    blocked_tables = []
    table_assignments = TableAssignment.query.all()
    for ta in table_assignments:
        if ta.verein != invite.verein:  # Eigene Tische nicht als blockiert anzeigen
            blocked_tables.append(ta.tischnummer)
    
    # Bestehende Tischzuweisung
    current_table = invite.tischnummer if invite.manuell_gesetzt else None
    
    return render_template(
        "assign_table.html", 
        invite=invite, 
        blocked=set(blocked_tables),  # Duplikate entfernen
        max_tables=max_tables,
        current_table=current_table,
        response=response,
        max_persons_per_table=max_persons_per_table
    )
