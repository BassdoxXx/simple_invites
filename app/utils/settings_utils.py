"""
Hilfsfunktionen für die Verwaltung von Anwendungseinstellungen.
"""

import os
from functools import lru_cache
from app.models import Setting

# Cache settings for 60 seconds to reduce DB queries
# Why: Settings rarely change but are accessed frequently
@lru_cache(maxsize=32)
def get_setting(key, default=None, expire_after=60):
    """
    Holt eine Einstellung aus der Datenbank mit Caching.
    
    Args:
        key: Der Schlüssel für die Einstellung
        default: Standardwert, wenn die Einstellung nicht gefunden wird
        expire_after: Cache-Zeit in Sekunden (nicht verwendet, aber für API-Konsistenz)
        
    Returns:
        Der Wert der Einstellung oder der Standardwert
    """
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default


def get_multiple_settings(setting_definitions):
    """Get multiple settings at once, using cached values.
    
    Why: Reduces code duplication when multiple settings are needed
    in a single context, while still benefiting from caching.
    
    Args:
        setting_definitions: Dict mapping setting keys to their default values
        
    Returns:
        Dict containing all requested settings with their values
    """
    return {key: get_setting(key, default) for key, default in setting_definitions.items()}


def get_max_tables():
    """Get maximum number of tables from settings.
    
    Why: This is a frequently accessed value that impacts table assignments
    and validations throughout the application.
    """
    max_tables_setting = get_setting("max_tables", "90")
    return int(max_tables_setting) if max_tables_setting.isdigit() else 90


def get_base_url():
    """Get base URL from APP_HOSTNAME environment variable or database setting.
    
    Why: We need a consistent way to generate absolute URLs throughout
    the application, prioritizing the environment variable to support
    different deployment environments.
    
    Returns:
        str: The base URL to use for all absolute links.
    """
    # 1. Try to get from environment variable first
    app_hostname = os.environ.get("APP_HOSTNAME")
    if app_hostname:
        return app_hostname
        
    # 2. Fall back to database setting
    base_url = get_setting("base_url", "http://localhost:5000")
    return base_url


def check_hostname_config():
    """
    Überprüft die Hostnamen-Konfiguration und gibt Warnungen aus,
    wenn sie nicht korrekt ist.
    
    Diese Funktion wird beim Startup aufgerufen, um Konfigurationsprobleme
    frühzeitig zu erkennen.
    """
    base_url = get_base_url()
    app_hostname = os.environ.get("APP_HOSTNAME")
    
    print("\n" + "="*60)
    print("🌐 HOSTNAME CONFIGURATION")
    print("="*60)
    
    if app_hostname:
        print(f"✅ APP_HOSTNAME environment variable is set to: {app_hostname}")
        print(f"✅ All links will be generated using: {base_url}")
    else:
        print("⚠️  WARNING: APP_HOSTNAME environment variable is NOT set!")
        print(f"⚠️  Using fallback from database: {base_url}")
        print("⚠️  This may cause incorrect URLs in production!")
        print("\n📝 Set APP_HOSTNAME in your environment or docker-compose.yml:")
        print("   Example: APP_HOSTNAME=https://invites.ffw-windischletten.de")
    
    print("="*60)
