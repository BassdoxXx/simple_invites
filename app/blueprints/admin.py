from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Invite, Response, Setting, TableAssignment, db
from app.utils.table_utils import assign_all_tables, get_blocked_tischnummern, get_next_free_tischnummer, build_verein_tische_map
from app.utils.settings_utils import get_setting, get_multiple_settings, get_max_tables, get_base_url
from app.utils.qr_utils import generate_qr
import os
from datetime import datetime, date
from sqlalchemy import func
from functools import lru_cache  # Für die cache_clear Methode

admin_bp = Blueprint("admin", __name__)

# Hinweis: Die Hilfsfunktionen für Einstellungen und Tischverwaltung wurden in 
# app/utils/settings_utils.py und app/utils/table_utils.py ausgelagert

# Bestehende Index-Route ohne Formularverarbeitung
@admin_bp.route("/", methods=["GET"])
@login_required
def index():
    """Admin dashboard for managing invitations."""
    invites = Invite.query.order_by(Invite.verein).all()
    responses = {r.token: r for r in Response.query.all()}
    max_tables = get_max_tables()

    # Prepare statistics and data for the template
    settings = get_multiple_settings({
        "enable_tables": "false",
        "max_tables": "90",
        "vereins_name": "",
        "event_name": "",
        "event_date": ""
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

    # Calculate days until event
    days_until_event = None
    event_date_str = settings["event_date"]
    event_name = settings["event_name"]
    
    if event_date_str:
        from datetime import datetime, date
        try:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            today = date.today()
            days_until_event = (event_date - today).days
        except ValueError:
            # Falls das Datumsformat nicht korrekt ist, ignorieren
            pass
    
    return render_template(
        "admin_dashboard.html",
        invites=invites,
        responses=responses,
        response_count=response_count,
        total_invites=total_invites,
        total_persons=total_persons,
        vereins_name=settings["vereins_name"],
        event_name=event_name,
        event_date=event_date_str,
        days_until_event=days_until_event,
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
        
        # Get contact information
        ansprechpartner = request.form.get("ansprechpartner", "").strip()
        strasse = request.form.get("strasse", "").strip()
        plz = request.form.get("plz", "").strip()
        ort = request.form.get("ort", "").strip()
        
        # Entweder Token vom Formular nehmen oder einen 8-stelligen generieren
        form_token = request.form.get("token", "").strip()
        if form_token and len(form_token) == 8:
            token = form_token
        else:
            # Generiere einen einzigartigen Token
            from app.utils.csv_utils import generate_unique_token
            token = generate_unique_token()
        
        # Base URL for response and QR code
        base_url = get_base_url()
        
        if invite:
            # Bestehende Einladung aktualisieren
            
            # Prüfen, ob der neue Vereinsname bereits existiert (wenn er geändert wurde)
            if verein.lower() != invite.verein.lower():
                existing_invite = Invite.query.filter(func.lower(Invite.verein) == verein.lower()).first()
                if existing_invite and existing_invite.id != invite.id:
                    flash(f"Ein Eintrag für '{verein}' existiert bereits. Bitte wählen Sie einen anderen Namen.", "danger")
                    return render_template(
                        "admin_invite_create.html", 
                        invite=invite,
                        vereins_name=get_setting("vereins_name", "")
                    )
            
            # Update invitation details
            invite.verein = verein
            invite.ansprechpartner = ansprechpartner
            invite.strasse = strasse
            invite.plz = plz
            invite.ort = ort
            
            # The token cannot be changed after creation
            
            # Save changes
            db.session.commit()
            
            flash(f"Einladung für {verein} wurde aktualisiert.", "success")
        else:
            # Prüfen, ob der Vereinsname bereits existiert
            existing_invite = Invite.query.filter(func.lower(Invite.verein) == verein.lower()).first()
            if existing_invite:
                flash(f"Ein Eintrag für '{verein}' existiert bereits. Bitte wählen Sie einen anderen Namen.", "danger")
                return render_template(
                    "admin_invite_create.html", 
                    invite=None,
                    vereins_name=get_setting("vereins_name", "")
                )
                
            # Create response URL
            invite_url = f"{base_url}/respond/{token}"
            
            # Erstelle die neue Einladung mit allen erforderlichen Feldern
            new_invite = Invite(
                verein=verein, 
                token=token,
                link=invite_url,
                ansprechpartner=ansprechpartner,
                strasse=strasse,
                plz=plz,
                ort=ort
            )
            db.session.add(new_invite)
            db.session.commit()
            
            # We don't generate QR codes here anymore - they will be generated on-demand when creating PDFs
            flash(f"Neue Einladung für {verein} wurde erstellt.", "success")
        
        return redirect(url_for("admin.index"))
    
    # Lade den Vereinsnamen für die Anzeige
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    vereins_name = vereins_name_setting.value if vereins_name_setting else ""
    
    return render_template(
        "admin_invite_create.html", 
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
        
        # Remove the invitation
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
        "event_date": "",  # Format: YYYY-MM-DD für das Event-Datum
        "event_time": "",  # Format: HH:MM Uhr
        "event_location": "",  # Veranstaltungsort
        "contact_email": "",  # E-Mail-Adresse für Kontakt
        "contact_address": "",  # Adresse des Vereins für Briefkopf
        "contact_phone": "",  # Telefonnummer für Kontakt
        "website": "",  # Website des Vereins
        "max_tables": "90",
        "max_persons_per_table": "10",
        "enable_tables": "false"
    }
    
    if request.method == "POST":
        # Process all settings from the form
        for key in setting_definitions:
            # Spezialbehandlung für Checkboxen: wenn nicht gesendet, setze auf "false"
            if key == "enable_tables":
                value = "true" if key in request.form else "false"
            else:
                value = request.form.get(key, setting_definitions[key])
                
            setting = Setting.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
            else:
                db.session.add(Setting(key=key, value=value))
        
        db.session.commit()
        
        # Clear setting cache to ensure latest values are used
        get_setting.cache_clear()
        
        # Neu berechnen der Tischzuweisung, wenn die Tischverwaltung aktiviert ist
        if request.form.get("enable_tables") == "true":
            from app.utils.table_utils import assign_all_tables
            assign_all_tables()
        
        flash("Einstellungen gespeichert", "success")
        return redirect(url_for("admin.settings"))

    # Optimiert: Alle Einstellungen auf einmal abrufen
    current_settings = get_multiple_settings(setting_definitions)
    
    return render_template(
        "admin_settings_edit.html",
        **current_settings,
    )

@admin_bp.route("/export/csv", methods=["GET", "POST"])
@login_required
def export_all_csv():
    """Export all invitations and responses to a CSV file."""
    from app.utils.csv_utils import generate_all_invites_csv, generate_single_invite_csv
    
    # Hilfsfunktion für die URL-Generierung
    def get_full_link(token):
        return url_for("public.respond", token=token, _external=True)
    
    # Prüfen ob spezifische Tokens ausgewählt wurden
    if request.method == "POST" and request.form.getlist('selected_invites'):
        selected_tokens = request.form.getlist('selected_invites')
        
        # Wenn nur ein Token ausgewählt wurde, generiere einen einzelnen CSV-Export
        if len(selected_tokens) == 1:
            invite = Invite.query.filter_by(token=selected_tokens[0]).first_or_404()
            res = Response.query.filter_by(token=selected_tokens[0]).first()
            return generate_single_invite_csv(invite, res, get_full_link)
        
        # Mehrere ausgewählte Einladungen exportieren
        invites = Invite.query.filter(Invite.token.in_(selected_tokens)).order_by(Invite.verein).all()
        responses = {r.token: r for r in Response.query.filter(Response.token.in_(selected_tokens)).all()}
        
        return generate_all_invites_csv(invites, responses, get_full_link)
    
    # Standard: Alle exportieren
    invites = Invite.query.all()
    responses = {r.token: r for r in Response.query.all()}
    return generate_all_invites_csv(invites, responses, get_full_link)

@admin_bp.route("/export/csv/<token>")
@login_required
def export_single_csv(token):
    """Export a single invitation with its response to CSV."""
    from app.utils.csv_utils import generate_single_invite_csv
    
    invite = Invite.query.filter_by(token=token).first_or_404()
    res = Response.query.filter_by(token=token).first()
    
    # Hilfsfunktion für die URL-Generierung
    def get_full_link(token):
        return url_for("public.respond", token=token, _external=True)
    
    return generate_single_invite_csv(invite, res, get_full_link)

# Die neue edit_invite Route sollte so lauten:
@admin_bp.route("/edit/<token>", methods=["GET", "POST"])
@login_required
def edit_invite(token):
    """Edit an existing invitation."""
    invite = Invite.query.filter_by(token=token).first_or_404()
    
    if request.method == "POST":
        # Get form data
        verein = request.form.get("verein", "").strip()
        ansprechpartner = request.form.get("ansprechpartner", "").strip()
        strasse = request.form.get("strasse", "").strip()
        plz = request.form.get("plz", "").strip()
        ort = request.form.get("ort", "").strip()
        
        # Check if another invite with this name exists
        if verein.lower() != invite.verein.lower():
            existing = Invite.query.filter(func.lower(Invite.verein) == verein.lower(),
                                          Invite.id != invite.id).first()
            if existing:
                flash(f"Ein Eintrag für '{verein}' existiert bereits. Bitte wählen Sie einen anderen Namen.", "danger")
                return render_template("admin_invite_edit.html", invite=invite)
        
        # Update the invite
        invite.verein = verein
        invite.ansprechpartner = ansprechpartner
        invite.strasse = strasse
        invite.plz = plz
        invite.ort = ort
        
        db.session.commit()
        
        flash(f"Einladung für {verein} wurde aktualisiert.", "success")
        return redirect(url_for("admin.index"))
    
    return render_template("admin_invite_edit.html", invite=invite)

@admin_bp.route("/import-csv", methods=["POST"])
@login_required
def import_csv():
    """Import multiple invitations from a CSV file.
    
    The CSV file should have a column named 'Verein' or just one column
    with the association/guest names. For each name, a new invitation
    will be created with an automatically generated token.
    Duplicate names will be skipped.
    """
    from app.utils.csv_utils import validate_csv_file, process_csv_import
    
    if 'csv_file' not in request.files:
        flash("Keine Datei ausgewählt.", "danger")
        return redirect(url_for("admin.create_invite"))
    
    csv_file = request.files['csv_file']
    has_header = request.form.get('has_header') == 'on'
    
    # Validiere die CSV-Datei
    is_valid, content, dialect, error_redirect = validate_csv_file(csv_file)
    if not is_valid:
        return error_redirect
    
    # Verarbeite den Import
    base_url = get_base_url()
    imported_count = process_csv_import(content, dialect, has_header, base_url)
    
    if imported_count > 0:
        flash(f"{imported_count} Einladungen wurden erfolgreich importiert.", "success")
    else:
        flash("Es wurden keine neuen Einladungen importiert. Möglicherweise existieren alle Namen bereits.", "warning")
        
    return redirect(url_for("admin.index"))

@admin_bp.route("/assign_table/<token>", methods=["GET", "POST"])
@login_required
def assign_table(token):
    """Manually assign a table to an invitation."""
    invite = Invite.query.filter_by(token=token).first_or_404()
    
    # Überprüfe, ob Tischverwaltung aktiviert ist
    enable_tables = get_setting("enable_tables", "false")
    if enable_tables != "true":
        flash("Die Tischverwaltung ist deaktiviert. Bitte aktivieren Sie sie zuerst in den Einstellungen.", "warning")
        return redirect(url_for("admin.settings"))
    
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
        "admin_table_assign.html", 
        invite=invite, 
        blocked=set(blocked_tables),  # Duplikate entfernen
        max_tables=max_tables,
        current_table=current_table,
        response=response,
        max_persons_per_table=max_persons_per_table
    )
