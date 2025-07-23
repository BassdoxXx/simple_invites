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
    
    # Pfad anpassen für Windows-Kompatibilität
    if os.name == 'nt':  # Windows
        data_dir = os.path.join(os.environ.get('APPDATA', 'C:/temp'), "simple_invites")
    else:
        data_dir = "/data/simple_invites"
        
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
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
        
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
        db.create_all()
        
    return app