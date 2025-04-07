from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


db = SQLAlchemy()

class Invite(db.Model):
    __tablename__ = "invites"
    id = db.Column(db.Integer, primary_key=True)
    verein = db.Column(db.String(150), nullable=False)
    adresse = db.Column(db.String(200), nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    link = db.Column(db.String(512), nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Response(db.Model):
    __tablename__ = "responses"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), db.ForeignKey("invites.token"), nullable=False)
    attending = db.Column(db.String(10), nullable=False)  # "yes" oder "no"
    persons = db.Column(db.Integer, nullable=True)
    drinks = db.Column(db.String(150), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Setting(db.Model):
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    force_password_change = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)