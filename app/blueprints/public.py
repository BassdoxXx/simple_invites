from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Setting, Invite, Response, db
from datetime import datetime, timezone

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    return render_template("token_input.html")

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
        return "Ungültiger Link", 404

    # Einladungstext aus der Datenbank laden
    invite_header = Setting.query.filter_by(key="invite_header").first()
    invite_header_value = invite_header.value if invite_header else "Einladung"

    if request.method == "POST":
        # Verarbeite die Rückmeldung
        attending = request.form.get("attending")
        persons = int(request.form.get("persons", 0))
        drinks = request.form.get("drinks", "")
        response = Response.query.filter_by(token=token).first()
        if response:
            response.attending = attending
            response.persons = persons
            response.drinks = drinks
        else:
            response = Response(
                token=token,
                attending=attending,
                persons=persons,
                drinks=drinks
            )
            db.session.add(response)
        db.session.commit()
        flash("Antwort gespeichert. Danke!", "success")
        return redirect(url_for("public.respond", token=token))

    return render_template("respond.html", invite=invite, invite_header=invite_header_value)

@public_bp.route("/impressum")
def legal_impressum():
    return render_template("impressum.html")

@public_bp.route("/datenschutz")
def legal_datenschutz():
    return render_template("datenschutz.html")