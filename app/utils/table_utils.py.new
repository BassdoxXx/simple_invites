"""
Hilfsfunktionen für die Verwaltung von Tischen und Tischzuweisungen.
"""

from app.models import Invite, TableAssignment, Response, db
from app.utils.settings_utils import get_setting

def get_blocked_tischnummern():
    """Get all currently occupied table numbers.
    
    Why: We need to track all assigned table numbers to prevent duplicates,
    both from manual assignments and automatic distribution.
    """
    invites = Invite.query.all()
    # First collect manually assigned tables from invites
    blocked = set(int(i.tischnummer) for i in invites if i.tischnummer and i.tischnummer.isdigit())
    # Then add tables from automatic assignments
    blocked |= set(int(t.tischnummer) for t in TableAssignment.query.all() if str(t.tischnummer).isdigit())
    return blocked


def get_next_free_tischnummer(blocked, max_tables):
    """Find the next available table number.
    
    Why: When creating new invites or resetting table assignments,
    we need to find the lowest available table number to ensure efficient
    use of available tables.
    """
    for i in range(1, max_tables + 1):
        if i not in blocked:
            return str(i)
    return "1"  # Fallback if all tables are taken


def build_verein_tische_map():
    """Create a mapping of associations to their assigned tables.
    
    Why: This centralized function creates a consistent representation of
    table assignments that's used in multiple templates.
    """
    table_assignments = TableAssignment.query.all()
    verein_tische = {}
    for ta in table_assignments:
        verein_tische.setdefault(ta.verein, []).append(str(ta.tischnummer))
    return verein_tische


def assign_all_tables():
    """Automatically assign tables to all invites.
    
    This function handles both manual and automatic table assignments.
    It respects manually assigned tables and distributes remaining guests
    optimally across available tables.
    """
    # Check if table management is enabled
    enable_tables = get_setting("enable_tables", "false")
    if enable_tables != "true":
        print("⚠️ Table management is disabled. Skipping table assignment.")
        return
        
    MIN_GRUPPE = 3
    
    # Get settings from the database
    max_tables_value = get_setting("max_tables", "90")
    max_persons_value = get_setting("max_persons_per_table", "10")
    
    MAX_TISCHE = int(max_tables_value) if max_tables_value.isdigit() else 90
    MAX_PERSONS_PER_TABLE = int(max_persons_value) if max_persons_value.isdigit() else 10

    # Clear all previous table assignments
    TableAssignment.query.delete()
    db.session.commit()

    # Collect information about manually assigned tables
    invites_manuell = Invite.query.filter_by(manuell_gesetzt=True).all()
    manuell_vereine = {i.verein for i in invites_manuell}
    manuell_tische = set()  # Set of manually assigned table numbers
    
    # Map manual assignments to associations
    manuell_zuweisungen = {}  # {verein: {'tischnummer': X, 'personen': Y}}
    
    for invite in invites_manuell:
        if invite.tischnummer and invite.tischnummer.isdigit():
            tischnummer = int(invite.tischnummer)
            manuell_tische.add(tischnummer)
            
            # Find the number of persons for this association
            response = Response.query.filter_by(token=invite.token, attending="yes").first()
            personen = response.persons if response else 0
            
            manuell_zuweisungen[invite.verein] = {
                'tischnummer': tischnummer,
                'personen': personen
            }

    # Associations with confirmed attendance but without manual assignment
    responses = Response.query.filter_by(attending="yes").filter(Response.persons > 0).all()
    vereine = []
    for r in responses:
        invite = Invite.query.filter_by(token=r.token).first()
        if invite and invite.verein not in manuell_vereine:
            vereine.append({"verein": invite.verein, "personen": r.persons})

    vereine.sort(key=lambda x: -x["personen"])  # Sort by group size (larger groups first)

    # Tables: List with occupied seats and assignments
    tische = []  # e.g. [{"belegt": 5, "zuweisungen": [(verein, personen), ...], "nummer": 1}, ...]

    # Initialize all tables from 1 to MAX_TISCHE as empty
    for i in range(1, MAX_TISCHE + 1):
        tische.append({"belegt": 0, "zuweisungen": [], "nummer": i, "reserviert": False})

    # Phase 1: Process manually assigned tables
    for verein, info in manuell_zuweisungen.items():
        tischnummer = info['tischnummer']
        personen = info['personen']
        
        # Find the corresponding table in the list
        tisch_index = next((i for i, t in enumerate(tische) if t["nummer"] == tischnummer), None)
        if tisch_index is None:
            continue
        
        # Mark this table as reserved
        tische[tisch_index]["reserviert"] = True
        
        # If there are more persons than MAX_PERSONS_PER_TABLE, look for adjacent tables
        if personen > MAX_PERSONS_PER_TABLE:
            rest_personen = personen
            
            # First fill the main table
            platz_auf_haupttisch = min(MAX_PERSONS_PER_TABLE, rest_personen)
            tische[tisch_index]["belegt"] = platz_auf_haupttisch
            tische[tisch_index]["zuweisungen"].append((verein, platz_auf_haupttisch))
            rest_personen -= platz_auf_haupttisch
            
            # Now look for adjacent tables
            if rest_personen > 0:
                # Try adjacent tables first (tischnummer-1 or tischnummer+1)
                nachbarn = [tischnummer - 1, tischnummer + 1]
                for nachbar_nr in nachbarn:
                    if rest_personen <= 0:
                        break
                        
                    nachbar_index = next((i for i, t in enumerate(tische) if t["nummer"] == nachbar_nr and not t["reserviert"] and t["belegt"] == 0), None)
                    if nachbar_index is not None:
                        # Adjacent table found and available
                        platz_auf_nachbartisch = min(MAX_PERSONS_PER_TABLE, rest_personen)
                        tische[nachbar_index]["belegt"] = platz_auf_nachbartisch
                        tische[nachbar_index]["zuweisungen"].append((verein, platz_auf_nachbartisch))
                        tische[nachbar_index]["reserviert"] = True  # Reserve this table as well
                        manuell_tische.add(nachbar_nr)  # Add to the list of manually assigned tables
                        rest_personen -= platz_auf_nachbartisch
                
                # If there are still persons left, look for the next available table
                if rest_personen > 0:
                    for i, t in enumerate(tische):
                        if not t["reserviert"] and t["belegt"] == 0:
                            platz_auf_freiem_tisch = min(MAX_PERSONS_PER_TABLE, rest_personen)
                            tische[i]["belegt"] = platz_auf_freiem_tisch
                            tische[i]["zuweisungen"].append((verein, platz_auf_freiem_tisch))
                            tische[i]["reserviert"] = True
                            manuell_tische.add(t["nummer"])
                            rest_personen -= platz_auf_freiem_tisch
                            if rest_personen <= 0:
                                break
        else:
            # Normal assignment if number of persons <= MAX_PERSONS_PER_TABLE
            tische[tisch_index]["belegt"] = personen
            tische[tisch_index]["zuweisungen"].append((verein, personen))

    # Phase 2: Automatic distribution for non-manual assignments
    for v in vereine:
        personen = v["personen"]
        verein_name = v["verein"]
        rest = personen

        while rest > 0:
            # Look for a table with enough space that is not reserved
            gefunden = False
            for tisch in tische:
                if tisch["reserviert"]:
                    continue
                    
                frei = MAX_PERSONS_PER_TABLE - tisch["belegt"]
                if frei > 0:
                    setze = min(frei, rest)
                    if setze < MIN_GRUPPE and rest >= MIN_GRUPPE:
                        continue
                    tisch["zuweisungen"].append((verein_name, setze))
                    tisch["belegt"] += setze
                    rest -= setze
                    gefunden = True
                    break
                    
            if not gefunden:
                # If no suitable table was found, look for a completely free table
                freier_tisch = next((t for t in tische if not t["reserviert"] and t["belegt"] == 0), None)
                if freier_tisch:
                    setze = min(MAX_PERSONS_PER_TABLE, rest)
                    freier_tisch["zuweisungen"].append((verein_name, setze))
                    freier_tisch["belegt"] += setze
                    rest -= setze
                else:
                    # If all available tables are full, we can't do anything more
                    print(f"⚠️ Warning: Not enough tables for {verein_name}, {rest} persons could not be placed.")
                    break

    # Write all assignments to the database
    TableAssignment.query.delete()
    db.session.commit()
    
    for tisch in tische:
        for verein, personen in tisch["zuweisungen"]:
            if personen > 0:  # Only save meaningful assignments
                db.session.add(TableAssignment(
                    tischnummer=tisch["nummer"], 
                    verein=verein, 
                    personen=personen
                ))
    
    db.session.commit()

    # Count the actual assignments for debug output
    assignment_count = TableAssignment.query.count()
    print("🔄 Table assignment is being recalculated...")
    print(f"✅ Table assignment completed. {assignment_count} assignments created.")
