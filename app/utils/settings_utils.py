"""
Hilfsfunktionen für die Verwaltung von Anwendungseinstellungen.
"""

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
