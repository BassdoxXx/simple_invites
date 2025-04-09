from flask import redirect, url_for, request
from flask_login import current_user

def enforce_password_change():
    if current_user.is_authenticated and current_user.force_password_change:
        # Verhindere Zugriff auf andere Seiten außer der Passwortänderungsseite
        if not (request.endpoint == "auth.change_password" or request.endpoint == "auth.logout"):
            return redirect(url_for("auth.change_password"))