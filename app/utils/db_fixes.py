"""
This is a temporary file with model fixes to handle missing database columns.
"""

import sqlalchemy as sa
from sqlalchemy import inspect
from flask import current_app

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        insp = inspect(engine)
        columns = [c['name'] for c in insp.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        current_app.logger.error(f"Error checking column {column_name}: {e}")
        return False

def apply_model_fixes(db, app):
    """Apply fixes to handle missing columns in the database"""
    with app.app_context():
        # Check if columns exist, if not, add them to the table
        engine = db.engine
        
        # List of columns we need to check for in the invites table
        columns_to_check = [
            ('ansprechpartner', sa.String(200)),
            ('strasse', sa.String(200)),
            ('plz', sa.String(10)),
            ('ort', sa.String(200)),
            ('telefon', sa.String(50)),
            ('email', sa.String(200)),
            ('qr_code_path', sa.String(512))
        ]
        
        # Check each column and add if missing
        for column_name, column_type in columns_to_check:
            if not check_column_exists(engine, 'invites', column_name):
                app.logger.warning(f"Column '{column_name}' is missing, attempting to add it")
                try:
                    with engine.begin() as connection:
                        connection.execute(sa.text(f"ALTER TABLE invites ADD COLUMN {column_name} {column_type}"))
                    app.logger.info(f"Added column '{column_name}' to invites table")
                except Exception as e:
                    app.logger.error(f"Failed to add column '{column_name}': {e}")
