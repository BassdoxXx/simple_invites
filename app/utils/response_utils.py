from app.models import Response, db
from datetime import datetime, timezone

def validate_person_count(persons):
    """
    Validates the number of persons.
    Args:
        persons (int): The number of persons.
    Returns:
        bool: True if valid, False otherwise.
    """
    return 1 <= persons <= 100

def save_response(response, token, attending, persons, drinks):
    """
    Saves or updates a response in the database.
    Args:
        response (Response): The existing response object (if any).
        token (str): The token associated with the invite.
        attending (str): Attendance status ("yes" or "no").
        persons (int): Number of persons attending.
        drinks (str): Drink preferences.
    """
    if not validate_person_count(persons):
        raise ValueError("Die Anzahl der Personen muss größer als 0 sein.")
    
    if response:
        response.attending = attending
        response.persons = persons
        response.drinks = drinks
        response.timestamp = datetime.now(timezone.utc)
    else:
        response = Response(
            token=token,
            attending=attending,
            persons=persons,
            drinks=drinks,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(response)
    db.session.commit()