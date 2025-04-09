from flask import redirect, url_for, request
from flask_login import current_user

def enforce_password_change():
    if current_user.is_authenticated and current_user.force_password_change:
        allowed_endpoints = ["auth.change_password", "auth.logout", "static"]
        if request.endpoint not in allowed_endpoints:
            return redirect(url_for("auth.change_password"))