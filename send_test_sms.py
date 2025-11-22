# send_test_sms.py
from twilio.rest import Client
from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_WHATSAPP_NUMBER
import socket

def is_network_available(host="api.twilio.com", port=443, timeout=5):
    """Check if Twilio API is reachable"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except OSError:
        return False

def send_whatsapp(to_number, message_body):
    """Send WhatsApp message via Twilio sandbox"""
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_WHATSAPP_NUMBER:
        print("❌ Twilio credentials or WhatsApp number missing.")
        return False

    if not is_network_available():
        print("⚠️ Cannot reach Twilio API. Check your internet or firewall.")
        return False

    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            body=message_body,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{to_number}"
        )
        print(f"✅ WhatsApp sent! SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"⚠️ WhatsApp failed: {e}")
        return False

def send_sms(to_number, message_body):
    """Send SMS via Twilio"""
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_NUMBER:
        print("❌ Twilio credentials or SMS number missing.")
        return False

    if not is_network_available():
        print("⚠️ Cannot reach Twilio API. Check your internet or firewall.")
        return False

    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            body=message_body,
            from_=TWILIO_NUMBER,
            to=to_number
        )
        print(f"✅ SMS sent! SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"⚠️ SMS failed: {e}")
        return False

if __name__ == "__main__":
    to_number = input("Enter destination phone (e.g., +2507XXXXXXX): ").strip()
    message_body = "✅ Test: Your Weather Alert System is connected successfully!"

    print("\nTrying WhatsApp first...")
    whatsapp_ok = send_whatsapp(to_number, message_body)

    if not whatsapp_ok:
        print("\nWhatsApp failed. Falling back to SMS...")
        sms_ok = send_sms(to_number, message_body)
        if not sms_ok:
            print("❌ Both WhatsApp and SMS failed. Check credentials, connectivity, and sandbox setup.")
