from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from app.models import Invite, Response, Setting, User, db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from app.qr_utils import generate_qr
import os
import uuid

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, '..', 'data', 'simple_invites.db')


def create_app(testing=False):
    """
    Erstellt und konfiguriert eine neue Flask-App-Instanz.
    Falls testing=True, wird eine In-Memory-SQLite-Datenbank genutzt.
    Diese Trennung erlaubt einfaches Testen ohne lokale Datei.
    """
    app = Flask(__name__)
    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "changeme123")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['HOSTNAME'] = os.environ.get("APP_HOSTNAME", "http://localhost:5000")

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    if not testing:
        with app.app_context():
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            if not os.path.exists(db_path):
                print("📂 Datenbank nicht gefunden. Erstelle neue Datenbank...")
                db.create_all()
                print("✅ Datenbank erstellt.")
            else:
                print("📁 Datenbank vorhanden. Prüfe Tabellen...")
                existing = db.inspect(db.engine).get_table_names()
                expected = ['invites', 'responses', 'settings', 'users']
                missing = [t for t in expected if t not in existing]
                if missing:
                    print(f"⚠️ Fehlende Tabellen: {missing} – werden ergänzt.")
                    db.create_all()
                    print("✅ Tabellen ergänzt.")

            if User.query.count() == 0:
                default_pw = "admin123"
                admin = User(username="admin")
                admin.set_password(default_pw)
                admin.force_password_change = True
                db.session.add(admin)
                db.session.commit()
                print("👤 Admin-User 'admin' mit Passwort 'admin123' wurde angelegt.")

    return app


app = create_app()


@app.route("/")
def index():
    return render_template("token_input.html")


@app.route("/find", methods=["POST"])
def find_token():
    token = request.form.get("token")
    if token:
        return redirect(url_for("respond", token=token))
    flash("Bitte einen gültigen Token eingeben.", "danger")
    return redirect(url_for("index"))


@app.before_request
def enforce_password_change():
    """
    Erzwingt eine Passwortänderung beim ersten Login. 
    Leitet zu /change-password um, wenn force_password_change aktiv ist.
    """
    if current_user.is_authenticated:
        if current_user.force_password_change:
            allowed_endpoints = ["change_password", "logout", "static"]
            if request.endpoint not in allowed_endpoints:
                return redirect(url_for("change_password"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if user.force_password_change:
                return redirect(url_for("change_password"))
            return redirect(url_for("admin"))
        flash("Login fehlgeschlagen", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Erfolgreich abgemeldet", "success")
    return redirect(url_for("login"))


@app.route("/admin/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Formular zur Passwortänderung, insbesondere für den ersten Login.
    """
    if request.method == "POST":
        pw1 = request.form.get("new_password")
        pw2 = request.form.get("confirm_password")

        if not pw1 or pw1 != pw2:
            flash("Die Passwörter stimmen nicht überein.", "danger")
            return render_template("change_password.html")

        current_user.set_password(pw1)
        current_user.force_password_change = False
        db.session.commit()
        flash("Passwort geändert", "success")
        return redirect(url_for("admin"))

    return render_template("change_password.html")


@app.route("/admin")
@login_required
def admin():
    """
    Admin-Startseite: Zeigt Einladungen, Rückmeldungen und Gästeübersicht.
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


@app.route("/admin/create", methods=["GET"])
@login_required
def create_invite():
    return render_template("invite_form.html")


@app.route("/admin/create", methods=["POST"])
@login_required
def new_invite():
    """
    Legt neue Einladung an. Optional kann ein bestehender Token übergeben werden,
    falls z.  eine Einladung gelöscht und erneut erstellt werden muss.
    """
    verein = request.form.get("verein")
    adresse = request.form.get("adresse")  # wird ggf. als Token interpretiert

    token = adresse.strip() if adresse else uuid.uuid4().hex[:10]
    link = f"{app.config['HOSTNAME']}/respond/{token}"
    qr_path = generate_qr(link, token)

    invite = Invite(
        verein=verein,
        adresse="",  # wird nicht verwendet
        token=token,
        link=link,
        qr_code_path=qr_path,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(invite)
    db.session.commit()
    flash("Einladung erstellt", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<token>", methods=["POST"])
@login_required
def delete_invite(token):
    """
    Löscht eine bestehende Einladung und ggf. die zugehörige Antwort.
    Löscht zusätzlich den zugehörigen QR-Code vom Dateisystem.
    """
    invite = Invite.query.filter_by(token=token).first()
    response = Response.query.filter_by(token=token).first()

    if invite:
        try:
            qr_path = os.path.join(BASE_DIR, 'static', 'qrcodes', os.path.basename(invite.qr_code_path))
            if os.path.exists(qr_path):
                os.remove(qr_path)
        except Exception as e:
            print(f"⚠️ QR-Code konnte nicht gelöscht werden: {e}")
        db.session.delete(invite)
    if response:
        db.session.delete(response)

    db.session.commit()
    flash("Einladung gelöscht", "success")
    return redirect(url_for("admin"))


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    """
    Ermöglicht dem Admin, API-Zugangsdaten für WhatsApp zu speichern.
    """
    phone_setting = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey_setting = Setting.query.filter_by(key="whatsapp_apikey").first()
    whatsapp_active = phone_setting and apikey_setting and phone_setting.value and apikey_setting.value

    if request.method == "POST":
        phone = request.form.get("phone")
        apikey = request.form.get("apikey")

        if phone_setting:
            phone_setting.value = phone
        else:
            db.session.add(Setting(key="whatsapp_phone", value=phone))

        if apikey_setting:
            apikey_setting.value = apikey
        else:
            db.session.add(Setting(key="whatsapp_apikey", value=apikey))

        db.session.commit()
        flash("Einstellungen gespeichert", "success")
        return redirect(url_for("admin_settings"))

    return render_template("admin_settings.html",
                           phone=phone_setting.value if phone_setting else "",
                           apikey=apikey_setting.value if apikey_setting else "",
                           whatsapp_active=whatsapp_active)


@app.route("/respond/<token>", methods=["GET", "POST"])
def respond(token):
    """
    Öffentlich zugängliches Formular zum Antworten auf eine Einladung.
    Ermöglicht Änderungen bis kurz vor dem Event.
    """
    invite = Invite.query.filter_by(token=token).first()
    if not invite:
        return "Ungültiger Link", 404

    response = Response.query.filter_by(token=token).first()

    if request.method == "POST":
        try:
            attending = request.form.get("attending")
            persons = int(request.form.get("persons", 0))
            if persons < 1 or persons > 100:
                flash("Die Anzahl der Personen muss zwischen 1 und 100 liegen.", "danger")
                return render_template("respond.html", invite=invite, response=response)

            drinks = request.form.get("drinks", "")

            if response:
                response.attending = attending
                response.persons = persons
                response.drinks = drinks
                response.timestamp = datetime.now(timezone.utc)
            else:
                response = Response(
                    token=token,
                    attending=attending,
                    persons=persons,
                    drinks=drinks,
                    timestamp=datetime.now(timezone.utc)
                )
                db.session.add(response)

            db.session.commit()
            flash("Antwort gespeichert. Danke!", "success")
            return redirect(url_for("respond", token=token))

        except ValueError:
            flash("Ungültige Eingabe bei der Personenanzahl.", "danger")
            return render_template("respond.html", invite=invite, response=response)

    return render_template("respond.html", invite=invite, response=response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
