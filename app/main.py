from app import create_app, db
from flask import render_template

app = create_app()

with app.app_context():
    db.create_all()  # Erstellt alle Tabellen, falls sie nicht existieren

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)