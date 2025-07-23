from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Invite(db.Model):
    """
    Speichert Einladungen zu einer Veranstaltung.
    Jeder Eintrag enthält einen Token und QR-Code-Link,
    über den eine spezifische Feuerwehr antworten kann.
    """
    __tablename__ = "invites"
    id = db.Column(db.Integer, primary_key=True)
    verein = db.Column(db.String(150), nullable=False)
    tischnummer = db.Column(db.String(200), nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    link = db.Column(db.String(512), nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Response(db.Model):
    """
    Speichert die Rückmeldungen (Antworten) zu Einladungen.
    Verknüpft über den Token mit der Invite-Tabelle.
    """
    __tablename__ = "responses"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), db.ForeignKey("invites.token"), nullable=False)
    attending = db.Column(db.String(10), nullable=False)  # "yes" oder "no"
    persons = db.Column(db.Integer, nullable=True)
    drinks = db.Column(db.String(150), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Setting(db.Model):
    """
    Universelle Key-Value Tabelle für Konfigurationen wie z.B. WhatsApp API-Daten.
    Ermöglicht flexible Erweiterung um weitere Einstellungen.
    """
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

class User(db.Model, UserMixin):
    """
    Einfache Benutzerverwaltung für Admin-Login.
    Unterstützt Passwortänderung beim ersten Login.
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    force_password_change = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Erstellt einen sicheren Hash für das neue Passwort."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vergleicht Eingabe mit dem gespeicherten Passwort-Hash."""
        return check_password_hash(self.password_hash, password)
