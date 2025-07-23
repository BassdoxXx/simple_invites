from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect  # Neuer Import
from app.models import User, db
from app.utils.enforce_password_change import enforce_password_change
from app.blueprints.auth import auth_bp
from app.blueprints.admin import admin_bp
from app.blueprints.public import public_bp
import os
import secrets

def create_app(testing=False):
    app = Flask(__name__)
    
    # SERVER_NAME und URL_SCHEME aus Umgebungsvariablen setzen
    app_hostname = os.environ.get("APP_HOSTNAME")
    if app_hostname:
        if app_hostname.startswith("https://"):
            app.config['SERVER_NAME'] = app_hostname.replace("https://", "")
            app.config['PREFERRED_URL_SCHEME'] = 'https'
        elif app_hostname.startswith("http://"):
            app.config['SERVER_NAME'] = app_hostname.replace("http://", "")
            app.config['PREFERRED_URL_SCHEME'] = 'http'
        else:
            app.config['SERVER_NAME'] = app_hostname
            app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Datenbank im Projektverzeichnis speichern
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance'))
    os.makedirs(data_dir, exist_ok=True)
        
    db_path = os.path.join(data_dir, "simple_invites.db")
    secret_file = os.path.join(data_dir, "secret_key.txt")

    # Ordner anlegen, falls nicht vorhanden
    os.makedirs(data_dir, exist_ok=True)

    # SECRET_KEY laden oder generieren
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                secret_key = f.read().strip()
        else:
            secret_key = secrets.token_hex(32)
            with open(secret_file, "w") as f:
                f.write(secret_key)
    app.config['SECRET_KEY'] = secret_key

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' if testing else f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.before_request(enforce_password_change)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(public_bp)

    # CSRF-Schutz aktivieren
    csrf = CSRFProtect(app)
    
    # Für APIs ausschließen (falls nötig)
    @csrf.exempt
    def api_exempt():
        pass  # Definiere hier API-Routen, falls vorhanden

    # Benutzerdefinierte Fehlerseiten
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error_404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error_500.html'), 500
        
    # CSP-Header hinzufügen
    @app.after_request
    def add_security_headers(response):
        # CSP anpassen, um Tailwind CDN zu erlauben
        if response.mimetype == 'text/html':
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "font-src 'self' data:; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
            response.headers['Content-Security-Policy'] = csp
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    with app.app_context():
        # Datenbank initialisieren
        db.create_all()
        
        # Prüfen, ob Admin-Benutzer existiert
        from app.models import User
        from datetime import datetime
        
        user_count = User.query.count()
        if user_count == 0:
            # Admin-Benutzer erstellen
            admin_user = User(
                username="admin",
                force_password_change=True
            )
            # Setze das Passwort
            admin_user.set_password("changeme")
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("="*50)
            print("ADMIN USER CREATED:")
            print("Username: admin")
            print("Password: changeme")
            print("Please change your password after first login.")
            print("="*50)
            
        # Füge einen globalen Kontext-Prozessor hinzu
        @app.context_processor
        def inject_now():
            return {'now': datetime.now()}
        
    app.config["SERVER_NAME"] = "invites.ffw-windischletten.de"  # oder mit Port: "deinedomain.de:443"
    app.config["PREFERRED_URL_SCHEME"] = "https"
    
    return app