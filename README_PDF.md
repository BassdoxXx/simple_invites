# PDF Einladungsgenerator - Dokumentation

## Neue Funktionalitäten

1. **QR-Code-Generierung** (optional):
   - QR-Codes können für jeden Einladungslink erstellt werden
   - Pfade werden in der Datenbank gespeichert
   - Funktion zum erneuten Generieren aller QR-Codes

2. **Erweiterte Datenbank**:
   - Kontaktinformationen für jeden Verein (Ansprechpartner, Adresse, usw.)
   - QR-Code-Pfad in der Datenbank gespeichert

3. **PDF-Generierung**:
   - Einzelne PDF-Einladungen pro Verein
   - Gesamtes PDF mit allen Einladungen
   - Professionelles Layout mit Link zur Antwortseite

4. **Erweiterter CSV-Import/Export**:
   - Unterstützt alle neuen Kontaktfelder
   - Optional: QR-Code-Generierung beim Import

## Installation

1. **Abhängigkeiten installieren**:
   ```
   pip install -r requirements.txt
   ```

2. **Falls es Probleme mit Pillow gibt, kann es separat installiert werden**:
   ```
   pip install fpdf==1.7.2
   ```

3. **Datenbank-Migration ausführen**:
   ```
   flask db upgrade
   ```

## Anwendung

### PDF-Einladungen

1. Im Admin-Dashboard gibt es einen neuen Bereich "PDF-Einladungen generieren"
2. Dort können Sie entweder alle Einladungen als PDF generieren oder einzelne
3. Die PDFs enthalten einen klickbaren Link zur Antwortseite
4. Optional können QR-Codes separat generiert und verteilt werden

### Kontaktdaten bearbeiten

1. Klicken Sie auf "Bearbeiten" neben einer Einladung
2. Sie können Ansprechpartner, Adresse und weitere Kontaktdaten hinzufügen
3. Diese Daten werden im PDF verwendet und können im CSV exportiert werden

### CSV-Import/Export

1. Der CSV-Import erkennt nun Spalten für Kontaktdaten
2. Der CSV-Export enthält alle neuen Felder
3. QR-Codes werden automatisch beim Import generiert

## Technische Details

### Neue Dateien

- `app/utils/pdf_utils.py`: PDF-Generierungsfunktionalität (verwendet FPDF)
- `app/blueprints/pdf.py`: Routen für die PDF-Generierung
- `app/templates/generate_pdfs.html`: UI für PDF-Generierung
- `app/templates/edit_contact.html`: UI für Kontaktdaten-Bearbeitung

### Geänderte Dateien

- `app/models.py`: Neue Felder für Kontaktdaten und QR-Code-Pfad
- `app/utils/qr_utils.py`: Verbesserte QR-Code-Generierung (optional)
- `app/utils/csv_utils.py`: Unterstützung für neue Felder
- `app/__init__.py`: Registrierung des neuen Blueprints
- `app/blueprints/admin.py`: Neue Route für Kontaktdaten-Bearbeitung
- `app/templates/admin_dashboard.html`: Links zu den neuen Funktionen
- `app/templates/admin_settings_edit.html`: Neue Felder für PDF-Einstellungen

### Datenbank-Migration

Eine neue Migration wurde erstellt, um die folgenden Felder zur `invites`-Tabelle hinzuzufügen:
- `ansprechpartner`
- `strasse`
- `plz`
- `ort`
- `telefon`
- `email`
- `qr_code_path`
