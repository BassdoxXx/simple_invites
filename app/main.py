from app import create_app, db
from flask import render_template
from flask_migrate import Migrate
from app.utils.settings_utils import check_hostname_config
from app.utils.db_fixes import apply_model_fixes
from app.utils.pdf_utils import cleanup_old_pdf_files
import threading
import time

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    # Apply database fixes if enabled
    if app.config.get('DB_AUTO_FIX', True):
        try:
            app.logger.info("Attempting to apply database fixes for missing columns...")
            apply_model_fixes(db, app)
        except Exception as e:
            app.logger.error(f"Error applying database fixes: {e}")
    
    # Überprüfe die Hostnamen-Konfiguration
    check_hostname_config()

# Background thread for periodic PDF cleanup
def periodic_pdf_cleanup():
    """Run PDF cleanup in a background thread at regular intervals"""
    with app.app_context():
        while True:
            try:
                # Get the configured cleanup interval from app config
                cleanup_minutes = app.config.get('PDF_CLEANUP_MINUTES', 15)
                
                # Run the cleanup function
                cleanup_old_pdf_files(cleanup_minutes)
                
                # Sleep for 5 minutes before next cleanup check
                time.sleep(300)  # 5 minutes in seconds
            except Exception as e:
                app.logger.error(f"Error in periodic PDF cleanup: {e}")
                time.sleep(300)  # Sleep on error too

if __name__ == "__main__":
    # Start the cleanup thread when running directly (not when imported)
    cleanup_thread = threading.Thread(target=periodic_pdf_cleanup)
    cleanup_thread.daemon = True  # Thread will exit when main thread exits
    cleanup_thread.start()
    
    app.run(host="0.0.0.0", port=5000, debug=True)