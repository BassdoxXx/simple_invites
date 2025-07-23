from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.models import User, db
from app.utils.enforce_password_change import enforce_password_change
from app.blueprints.auth import auth_bp
from app.blueprints.admin import admin_bp
from app.blueprints.public import public_bp
import os
import secrets

def create_app(testing=False):
    app = Flask(__name__)
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

    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin_user = User(username="admin")
            admin_user.set_password("changeme")
            admin_user.force_password_change = True
            db.session.add(admin_user)
            db.session.commit()

    return app