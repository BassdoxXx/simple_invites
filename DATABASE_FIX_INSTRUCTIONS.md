# Database Fix Instructions

## Problem Description

Your application is encountering errors related to missing database columns. These columns exist in your local development environment but not on the production server.

Error message example:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: invites.ansprechpartner
```

## Solution Implemented

I've added a temporary fix that will automatically detect and add missing columns to your database schema when the application starts. This includes:

1. A new module `app/utils/db_fixes.py` that:
   - Checks if required columns exist in the database
   - Adds missing columns automatically when the app starts
   
2. Configuration changes in `app/__init__.py` to enable this automatic fixing
   
3. Integration in `app/main.py` to apply these fixes during application startup

## How to Use

### Option 1: Automatic Fix (Recommended)

1. Upload the modified files to your server:
   - `app/utils/db_fixes.py`
   - `app/__init__.py`
   - `app/main.py`

2. Restart your application
   - The app will automatically attempt to add any missing columns

3. If you want to disable the automatic fixing, you can set the environment variable:
   ```
   DB_AUTO_FIX=False
   ```

### Option 2: Manual Migration (More Reliable)

If you prefer to use Flask's migration system for a more proper fix:

1. SSH into your server
2. Navigate to your application directory
3. Activate your virtual environment if you're using one:
   ```
   source venv/bin/activate  # Adjust path as needed
   ```
4. Run the database migrations:
   ```
   flask db upgrade
   ```
5. Restart your application

## Troubleshooting

If you encounter any issues:

1. Check the application logs for error messages
2. Ensure that the SQLite database file is writable by the application
3. Make a backup of your database before applying any changes
4. If automatic fixing fails, try the manual migration approach

## Long-term Recommendation

For a more robust solution:

1. Always use Flask-Migrate for schema changes
2. Run `flask db migrate` after model changes to generate migration scripts
3. Apply migrations with `flask db upgrade` in all environments
4. Consider implementing a deployment process that includes migration steps

This will ensure that your database schema stays synchronized across all environments.
