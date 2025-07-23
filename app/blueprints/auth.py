from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if user.force_password_change:
                return redirect(url_for("auth.change_password"))
            return redirect(url_for("admin.index"))
        flash("Login fehlgeschlagen", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Erfolgreich abgemeldet", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # Passwort-Validierung
        if len(new_password) < 8:
            flash("Das Passwort muss mindestens 8 Zeichen lang sein.")
            return render_template("change_password.html")
        
        if not any(c.isdigit() for c in new_password):
            flash("Das Passwort muss mindestens eine Zahl enthalten.")
            return render_template("change_password.html")
        
        if not any(c.isupper() for c in new_password):
            flash("Das Passwort muss mindestens einen Großbuchstaben enthalten.")
            return render_template("change_password.html")
        
        if new_password != confirm_password:
            flash("Die Passwörter stimmen nicht überein.")
            return render_template("change_password.html")
        
        # Passwort setzen und speichern
        current_user.set_password(new_password)
        current_user.force_password_change = False
        db.session.commit()
        
        flash("Passwort erfolgreich geändert.")
        return redirect(url_for("admin.index"))
    
    return render_template("change_password.html")