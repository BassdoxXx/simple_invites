from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Setting, Invite, Response, TableAssignment, db
from app.utils.tisch_utils import assign_all_tables
from datetime import datetime, timezone

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    return render_template(
        "token_input.html",
        vereins_name=vereins_name_setting.value if vereins_name_setting else "",
        event_name=event_name_setting.value if event_name_setting else ""
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

    # Einladungstext aus der Datenbank laden
    invite_header = Setting.query.filter_by(key="invite_header").first()
    invite_header_value = invite_header.value if invite_header else "Einladung"

    # Vorhandene Antwort abrufen
    response = Response.query.filter_by(token=token).first()

    if request.method == "POST":
        # Verarbeite die Rückmeldung
        attending = request.form.get("attending")
        persons = request.form.get("persons", "").strip()

        try:
            persons = int(persons) if persons else 0
        except ValueError:
            persons = 0

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
        db.session.commit()

        # Tischlogik nur bei Zusage und Personen > 0
        enable_tables_setting = Setting.query.filter_by(key="enable_tables").first()
        enable_tables = enable_tables_setting.value == "true" if enable_tables_setting else False
        if attending == "yes" and persons > 0 and enable_tables:
            assign_all_tables()  # Zentrale Tischvergabe

        flash("Antwort gespeichert. Danke!", "success")
        return redirect(url_for("public.respond", token=token))

    # Übergabe der vorhandenen Antwort an das Template
    event_name_setting = Setting.query.filter_by(key="event_name").first()
    vereins_name_setting = Setting.query.filter_by(key="vereins_name").first()
    return render_template(
        "respond.html",
        invite=invite,
        invite_header=invite_header_value,
        response=response,
        event_name=event_name_setting.value if event_name_setting else "",
        vereins_name=vereins_name_setting.value if vereins_name_setting else "",
        gast_name=invite.verein
    )

@public_bp.route("/impressum")
def legal_impressum():
    return render_template("impressum.html")

@public_bp.route("/datenschutz")
def legal_datenschutz():
    return render_template("datenschutz.html")
