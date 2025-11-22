# FILE: debug_config.py
from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER, OPENWEATHER_API_KEY, CITY
print("TWILIO_SID loaded:", bool(TWILIO_SID))
print("TWILIO_TOKEN loaded:", bool(TWILIO_TOKEN))
print("TWILIO_WHATSAPP_NUMBER loaded:", TWILIO_WHATSAPP_NUMBER or "<empty>")
print("TWILIO_NUMBER loaded:", TWILIO_NUMBER or "<empty>")
print("OPENWEATHER_API_KEY loaded:", bool(OPENWEATHER_API_KEY))
print("CITY:", CITY)