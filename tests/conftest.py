# tests/conftest.py
import pytest
from app.main import create_app
from app.models import db

@pytest.fixture
def test_client():
    app = create_app(testing=True)

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()