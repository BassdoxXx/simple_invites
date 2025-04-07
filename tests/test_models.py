# tests/test_models.py
from app.models import Invite, Response, db
from datetime import datetime, timezone

def test_invite_model(test_client):
    invite = Invite(
        verein="FFW Test",
        adresse="Testweg 1",
        token="abc123",
        link="https://test/respond/abc123",
        qr_code_path="static/qrcodes/abc123.png",
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(invite)
    db.session.commit()

    result = Invite.query.filter_by(token="abc123").first()
    assert result is not None
    assert result.verein == "FFW Test"

def test_response_model(test_client):
    response = Response(
        token="abc123",
        attending="yes",
        persons=5,
        drinks="2x Spezi",
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(response)
    db.session.commit()

    result = Response.query.filter_by(token="abc123").first()
    assert result is not None
    assert result.attending == "yes"
