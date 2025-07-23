def assign_all_tables():
    # Importiere die get_setting-Funktion für konsistenten Zugriff
    from app.blueprints.admin import get_setting
    from app.models import Response, TableAssignment, db, Invite

    MIN_GRUPPE = 3
    
    # Verwende die gecachte get_setting-Funktion anstatt direkter DB-Zugriffe
    max_tables_value = get_setting("max_tables", "90")
    max_persons_value = get_setting("max_persons_per_table", "10")
    
    MAX_TISCHE = int(max_tables_value) if max_tables_value.isdigit() else 90
    MAX_PERSONS_PER_TABLE = int(max_persons_value) if max_persons_value.isdigit() else 10

    # Alle bisherigen Zuweisungen löschen
    TableAssignment.query.delete()
    db.session.commit()

    # Sammle alle Informationen zu manuell gesetzten Tischen und deren Personenzahl
    invites_manuell = Invite.query.filter_by(manuell_gesetzt=True).all()
    manuell_vereine = {i.verein for i in invites_manuell}
    manuell_tische = set()  # Diese Menge sammelt alle manuell belegten Tischnummern
    
    # Ordne manuelle Zuweisungen den Vereinen zu
    manuell_zuweisungen = {}  # {verein: {'tischnummer': X, 'personen': Y}}
    
    for invite in invites_manuell:
        if invite.tischnummer and invite.tischnummer.isdigit():
            tischnummer = int(invite.tischnummer)
            manuell_tische.add(tischnummer)
            
            # Finde die Personenzahl für diesen Verein
            response = Response.query.filter_by(token=invite.token, attending="yes").first()
            personen = response.persons if response else 0
            
            manuell_zuweisungen[invite.verein] = {
                'tischnummer': tischnummer,
                'personen': personen
            }

    # Vereine mit Zusagen, aber ohne manuell_gesetzt
    responses = Response.query.filter_by(attending="yes").filter(Response.persons > 0).all()
    vereine = []
    for r in responses:
        invite = Invite.query.filter_by(token=r.token).first()
        if invite and invite.verein not in manuell_vereine:
            vereine.append({"verein": invite.verein, "personen": r.persons})

    vereine.sort(key=lambda x: -x["personen"])  # große Gruppen zuerst

    # Tische: Liste mit belegten Plätzen und Zuweisungen
    tische = []  # z.B. [{"belegt": 5, "zuweisungen": [(verein, personen), ...], "nummer": 1}, ...]

    # Initialisiere alle Tische von 1 bis MAX_TISCHE als leer
    for i in range(1, MAX_TISCHE + 1):
        tische.append({"belegt": 0, "zuweisungen": [], "nummer": i, "reserviert": False})

    # Erste Phase: Verarbeite die manuell zugewiesenen Tische
    for verein, info in manuell_zuweisungen.items():
        tischnummer = info['tischnummer']
        personen = info['personen']
        
        # Finde den entsprechenden Tisch in der Liste
        tisch_index = next((i for i, t in enumerate(tische) if t["nummer"] == tischnummer), None)
        if tisch_index is None:
            continue
        
        # Markiere diesen Tisch als reserviert
        tische[tisch_index]["reserviert"] = True
        
        # Wenn mehr Personen als MAX_PERSONS_PER_TABLE, suche benachbarte Tische
        if personen > MAX_PERSONS_PER_TABLE:
            rest_personen = personen
            
            # Zuerst den Haupttisch belegen
            platz_auf_haupttisch = min(MAX_PERSONS_PER_TABLE, rest_personen)
            tische[tisch_index]["belegt"] = platz_auf_haupttisch
            tische[tisch_index]["zuweisungen"].append((verein, platz_auf_haupttisch))
            rest_personen -= platz_auf_haupttisch
            
            # Jetzt nach benachbarten Tischen suchen
            if rest_personen > 0:
                # Versuche zuerst Nachbartische (tischnummer-1 oder tischnummer+1)
                nachbarn = [tischnummer - 1, tischnummer + 1]
                for nachbar_nr in nachbarn:
                    if rest_personen <= 0:
                        break
                        
                    nachbar_index = next((i for i, t in enumerate(tische) if t["nummer"] == nachbar_nr and not t["reserviert"] and t["belegt"] == 0), None)
                    if nachbar_index is not None:
                        # Nachbartisch gefunden und verfügbar
                        platz_auf_nachbartisch = min(MAX_PERSONS_PER_TABLE, rest_personen)
                        tische[nachbar_index]["belegt"] = platz_auf_nachbartisch
                        tische[nachbar_index]["zuweisungen"].append((verein, platz_auf_nachbartisch))
                        tische[nachbar_index]["reserviert"] = True  # Reserviere auch diesen Tisch
                        manuell_tische.add(nachbar_nr)  # Füge zur Liste der manuell belegten Tische hinzu
                        rest_personen -= platz_auf_nachbartisch
                
                # Wenn immer noch Personen übrig sind, suche den nächsten freien Tisch
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
            # Normal belegen, wenn Personenzahl <= MAX_PERSONS_PER_TABLE
            tische[tisch_index]["belegt"] = personen
            tische[tisch_index]["zuweisungen"].append((verein, personen))

    # Zweite Phase: Automatische Verteilung für nicht-manuelle Zuweisungen
    for v in vereine:
        personen = v["personen"]
        verein_name = v["verein"]
        rest = personen

        while rest > 0:
            # Suche einen Tisch mit genug Platz, der nicht reserviert ist
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
                # Wenn kein passender Tisch gefunden wurde, suche nach einem komplett freien Tisch
                freier_tisch = next((t for t in tische if not t["reserviert"] and t["belegt"] == 0), None)
                if freier_tisch:
                    setze = min(MAX_PERSONS_PER_TABLE, rest)
                    freier_tisch["zuweisungen"].append((verein_name, setze))
                    freier_tisch["belegt"] += setze
                    rest -= setze
                else:
                    # Wenn alle verfügbaren Tische voll sind, dann können wir leider nichts mehr tun
                    print(f"⚠️ Warnung: Nicht genügend Tische für {verein_name}, {rest} Personen konnten nicht platziert werden.")
                    break

    # Schreibe alle Zuweisungen in die DB
    TableAssignment.query.delete()
    db.session.commit()
    
    for tisch in tische:
        for verein, personen in tisch["zuweisungen"]:
            if personen > 0:  # Nur sinnvolle Zuweisungen speichern
                db.session.add(TableAssignment(
                    tischnummer=tisch["nummer"], 
                    verein=verein, 
                    personen=personen
                ))
    
    db.session.commit()

    # Zähle die tatsächlichen Zuweisungen für die Debug-Ausgabe
    assignment_count = TableAssignment.query.count()
    print("🔄 Tischzuweisung wird neu berechnet...")
    print(f"✅ Tischzuweisung abgeschlossen. {assignment_count} Zuweisungen erstellt.")