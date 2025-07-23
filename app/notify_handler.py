import requests
import urllib.parse
from app.models import Invite, Response, Setting, db


def get_whatsapp_settings():
    phone_setting = Setting.query.filter_by(key="whatsapp_phone").first()
    apikey_setting = Setting.query.filter_by(key="whatsapp_apikey").first()
    if phone_setting and apikey_setting:
        return phone_setting.value, apikey_setting.value
    return None, None

def send_whatsapp_message(text):
    phone, apikey = get_whatsapp_settings()
    if not phone or not apikey:
        print("WhatsApp-Benachrichtigung übersprungen (nicht konfiguriert).")
        return

    message = urllib.parse.quote(text)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={message}&apikey={apikey}"
    try:
        response = requests.get(url)
        if "Message sent successfully" not in response.text:
            print(f"Fehler bei WhatsApp: {response.text}")
    except Exception as e:
        print(f"Fehler bei WhatsApp-Sendung: {e}")
