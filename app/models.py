from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Invite(db.Model):
    """
    Speichert Einladungen zu einer Veranstaltung.
    Jeder Eintrag enthält einen Token und einen Link,
    über den eine spezifische Feuerwehr antworten kann.
    """
    __tablename__ = "invites"
    id = db.Column(db.Integer, primary_key=True)
    verein = db.Column(db.String(150), nullable=False)
    tischnummer = db.Column(db.String(200), nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    link = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    manuell_gesetzt = db.Column(db.Boolean, default=False)
    
    # Neue Felder für Kontaktdaten
    ansprechpartner = db.Column(db.String(200), nullable=True)
    strasse = db.Column(db.String(200), nullable=True)
    plz = db.Column(db.String(10), nullable=True)
    ort = db.Column(db.String(200), nullable=True)
    telefon = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    qr_code_path = db.Column(db.String(512), nullable=True)
    
    def __init__(self, **kwargs):
        # QR code path wird bei Bedarf später gesetzt
        super(Invite, self).__init__(**kwargs)

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
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Setting(db.Model):
    """
    Universelle Key-Value Tabelle für Konfigurationen wie z.B. WhatsApp API-Daten,
    maximale Tischanzahl (max_tables), Tisch-Logik aktiv/inaktiv (enable_tables) usw.
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

class TableAssignment(db.Model):
    __tablename__ = "table_assignments"
    id = db.Column(db.Integer, primary_key=True)
    tischnummer = db.Column(db.Integer, nullable=False)
    verein = db.Column(db.String(150), nullable=False)
    personen = db.Column(db.Integer, nullable=False)
