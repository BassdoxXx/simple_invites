def assign_all_tables():
    from app.models import Response, TableAssignment, Setting, db, Invite

    MIN_GRUPPE = 3
    max_tables_setting = Setting.query.filter_by(key="max_tables").first()
    max_persons_setting = Setting.query.filter_by(key="max_persons_per_table").first()
    MAX_TISCHE = int(max_tables_setting.value) if max_tables_setting else 90
    MAX_PERSONS_PER_TABLE = int(max_persons_setting.value) if max_persons_setting else 10

    # Alle bisherigen Zuweisungen löschen
    TableAssignment.query.delete()
    db.session.commit()

    # Manuell gesetzte Tische und Vereine
    invites_manuell = Invite.query.filter_by(manuell_gesetzt=True).all()
    manuell_vereine = {i.verein for i in invites_manuell}
    manuell_tische = {int(i.tischnummer) for i in invites_manuell if i.tischnummer and i.tischnummer.isdigit()}

    # Vereine mit Zusagen, aber ohne manuell_gesetzt
    responses = Response.query.filter_by(attending="yes").filter(Response.persons > 0).all()
    vereine = []
    for r in responses:
        invite = Invite.query.filter_by(token=r.token).first()
        if invite and invite.verein not in manuell_vereine:
            verein_name = invite.verein
            vereine.append({"verein": verein_name, "personen": r.persons})

    vereine.sort(key=lambda x: -x["personen"])  # große Gruppen zuerst

    # Tische: Liste mit belegten Plätzen und Zuweisungen
    tische = []  # z.B. [{"belegt": 5, "zuweisungen": [(verein, personen), ...], "nummer": 1}, ...]

    # Initialisiere die manuell vergebenen Tische als "belegt"
    for num in manuell_tische:
        tische.append({"belegt": MAX_PERSONS_PER_TABLE, "zuweisungen": [], "nummer": num})

    # Automatische Verteilung auf freie Tische
    next_tisch_nummer = 1
    for v in vereine:
        personen = v["personen"]
        verein_name = v["verein"]
        rest = personen

        while rest > 0:
            # Suche einen Tisch mit genug Platz, der nicht manuell vergeben ist
            gefunden = False
            for tisch in tische:
                if tisch["nummer"] in manuell_tische:
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
                # Finde nächste freie Tischnummer, die nicht manuell vergeben ist
                while next_tisch_nummer in manuell_tische or any(t["nummer"] == next_tisch_nummer for t in tische):
                    next_tisch_nummer += 1
                setze = min(MAX_PERSONS_PER_TABLE, rest)
                tische.append({"belegt": setze, "zuweisungen": [(verein_name, setze)], "nummer": next_tisch_nummer})
                rest -= setze

    # Schreibe alle Zuweisungen in die DB
    TableAssignment.query.delete()
    db.session.commit()
    for tisch in tische:
        for verein, personen in tisch["zuweisungen"]:
            db.session.add(TableAssignment(tischnummer=tisch["nummer"], verein=verein, personen=personen))
    db.session.commit()