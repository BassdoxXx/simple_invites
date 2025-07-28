from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Setting, Invite, Response, TableAssignment, db
from app.utils.table_utils import assign_all_tables
from datetime import datetime, timezone

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    # Get settings for the view
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    event_date_setting = Setting.query.filter_by(key="event_date").first()
    
    # Calculate days until event for countdown
    days_until_event = None
    event_date_formatted = None
    if event_date_setting and event_date_setting.value:
        try:
            event_date = datetime.strptime(event_date_setting.value, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_until_event = (event_date - today).days
            event_date_formatted = event_date.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            # Falls das Datumsformat nicht korrekt ist, ignorieren
            pass
            
    return render_template(
        "public_token_input.html",
        vereins_name=vereins_name_setting.value if vereins_name_setting else "",
        event_name=event_name_setting.value if event_name_setting else "",
        days_until_event=days_until_event,
        event_date=event_date_formatted
    )

@public_bp.route("/find", methods=["POST"])
def find_token():
    token = request.form.get("token")
    if token:
        return redirect(url_for("public.respond", token=token))
    flash("Bitte einen gültigen Token eingeben.", "danger")
    return redirect(url_for("public.index"))

@public_bp.route("/respond/<token>", methods=["GET", "POST"])
def respond(token):
    """
    Zeigt die Einladung an und verarbeitet die Rückmeldung.
    """
    invite = Invite.query.filter_by(token=token).first()
    if not invite:
        flash("Uuupsii! Diesen Token kennen wir nicht. Bitte überprüfe deine Eingabe.", "danger")
        return redirect(url_for("public.index"))
        
    # Get settings for the view
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    event_date_setting = Setting.query.filter_by(key="event_date").first()
    
    # Calculate days until event for countdown
    days_until_event = None
    event_date_formatted = None
    if event_date_setting and event_date_setting.value:
        try:
            event_date = datetime.strptime(event_date_setting.value, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_until_event = (event_date - today).days
            event_date_formatted = event_date.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            # Falls das Datumsformat nicht korrekt ist, ignorieren
            pass

    # Einladungstext aus der Datenbank laden
    invite_header = Setting.query.filter_by(key="invite_header").first()
    invite_header_value = invite_header.value if invite_header else "Einladung"

    # Vorhandene Antwort abrufen
    response = Response.query.filter_by(token=token).first()

    # Alte Werte für den Vergleich speichern
    old_attending = response.attending if response else None
    old_persons = response.persons if response else None

    if request.method == "POST":
        # Verarbeite die Rückmeldung
        attending = request.form.get("attending")
        persons = request.form.get("persons", "").strip()

        try:
            persons = int(persons) if persons else 0
        except ValueError:
            persons = 0
            
        # Bei "Nein"-Antworten Personenzahl auf 0 setzen
        if attending == "no":
            persons = 0
            
            # Bei "Nein" auch manuelle Tischzuweisung entfernen
            if invite.manuell_gesetzt:
                invite.manuell_gesetzt = False
                invite.tischnummer = None

        if response:
            response.attending = attending
            response.persons = persons
        else:
            response = Response(
                token=token,
                attending=attending,
                persons=persons
            )
            db.session.add(response)
            
        # Änderungen speichern
        db.session.commit()

        # Tische neu berechnen, wenn sich der Status oder die Personenzahl ändert
        attending_changed = old_attending != attending if old_attending else True
        persons_changed = old_persons != persons if old_persons else True

        if attending_changed or persons_changed:
            assign_all_tables()  # Zentrale Tischvergabe - berücksichtigt Aktivierungsstatus

        flash("Antwort gespeichert. Danke!", "success")
        return redirect(url_for("public.respond", token=token))

    # Übergabe der vorhandenen Antwort an das Template
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    return render_template(
        "public_invite_respond.html",
        invite=invite,
        invite_header=invite_header_value,
        response=response,
        event_name=event_name_setting.value if event_name_setting else "",
        vereins_name=vereins_name_setting.value if vereins_name_setting else "",
        gast_name=invite.verein,
        days_until_event=days_until_event,
        event_date=event_date_formatted
    )

@public_bp.route("/impressum")
def legal_impressum():
    # Get event info for countdown banner
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    event_date_setting = Setting.query.filter_by(key="event_date").first()
    
    # Calculate days until event for countdown
    days_until_event = None
    event_date_formatted = None
    if event_date_setting and event_date_setting.value:
        try:
            event_date = datetime.strptime(event_date_setting.value, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_until_event = (event_date - today).days
            event_date_formatted = event_date.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            pass
            
    return render_template(
        "public_legal_impressum.html",
        event_name=event_name_setting.value if event_name_setting else "",
        days_until_event=days_until_event,
        event_date=event_date_formatted
    )

@public_bp.route("/datenschutz")
def legal_datenschutz():
    # Get event info for countdown banner
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    event_date_setting = Setting.query.filter_by(key="event_date").first()
    
    # Calculate days until event for countdown
    days_until_event = None
    event_date_formatted = None
    if event_date_setting and event_date_setting.value:
        try:
            event_date = datetime.strptime(event_date_setting.value, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_until_event = (event_date - today).days
            event_date_formatted = event_date.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            pass
            
    return render_template(
        "public_legal_privacy.html",
        event_name=event_name_setting.value if event_name_setting else "",
        days_until_event=days_until_event,
        event_date=event_date_formatted
    )
