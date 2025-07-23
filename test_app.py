#!/usr/bin/env python3
"""
Test Script für Simple Invites
Überprüft die grundlegende Funktionalität der Anwendung
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Invite, Response, Setting

def test_basic_functionality():
    """Test der grundlegenden App-Funktionalität"""
    print("🧪 Testing Simple Invites Application...")
    
    # App im Test-Modus erstellen
    app = create_app(testing=True)
    
    with app.app_context():
        print("✅ App created successfully")
        
        # Datenbank initialisieren
        db.create_all()
        print("✅ Database initialized")
        
        # Test User erstellen
        test_user = User(username="testadmin")
        test_user.set_password("testpass")
        db.session.add(test_user)
        db.session.commit()
        print("✅ User creation works")
        
        # Test Invite erstellen
        test_invite = Invite(
            verein="Test Feuerwehr",
            token="test123",
            link="http://localhost:5000/respond/test123"
        )
        db.session.add(test_invite)
        db.session.commit()
        print("✅ Invite creation works")
        
        # Test Response erstellen
        test_response = Response(
            token="test123",
            attending="yes",
            persons=5
        )
        db.session.add(test_response)
        db.session.commit()
        print("✅ Response creation works")
        
        # Test Setting erstellen
        test_setting = Setting(
            key="test_setting",
            value="test_value"
        )
        db.session.add(test_setting)
        db.session.commit()
        print("✅ Settings work")
        
        print("🎉 All basic tests passed!")
        return True

if __name__ == "__main__":
    try:
        test_basic_functionality()
        print("\n✅ Simple Invites ist bereit für Production!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
