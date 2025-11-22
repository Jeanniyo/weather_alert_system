# FILE: quick_sms_test.py
from alert import TwilioMessenger
from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER
TARGET = "+250791117367"
m = TwilioMessenger(TWILIO_SID, TWILIO_TOKEN, whatsapp_from=None, sms_from=TWILIO_NUMBER)
try:
    res = m.send_sms(TARGET, "Test SMS from weather alert system")
    print("SMS sent, SID:", getattr(res, "sid", "unknown"))
except Exception as e:
    print("SMS failed:", e)