# FILE: config.py
# PURPOSE: Central configuration loaded from environment variables

import os
from dotenv import load_dotenv

# Load .env from the project folder
load_dotenv()

# ===== OpenWeather settings =====
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CITY = os.getenv("CITY", "Kigali,RW")

# ===== Twilio (SMS / WhatsApp) =====
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "")            # E.164, e.g., "+15005550006"
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # e.g., "+14155238886"

# ===== Email (SMTP) [optional] =====
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")

# ===== Firebase Cloud Messaging (optional) =====
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")

# ===== Alert thresholds =====
RAIN_POP_THRESHOLD = float(os.getenv("RAIN_POP_THRESHOLD", "0.6"))
RAINFALL_MM_THRESHOLD = float(os.getenv("RAINFALL_MM_THRESHOLD", "10.0"))

# ===== Default contacts CSV path =====
CONTACTS_CSV = os.getenv("CONTACTS_CSV", "contacts.csv")

# ===== Emergency thresholds and state =====
EMERGENCY_WIND_MS = float(os.getenv("EMERGENCY_WIND_MS", "12.0"))
EMERGENCY_TEMP_C = float(os.getenv("EMERGENCY_TEMP_C", "40.0"))
EMERGENCY_STATE_FILE = os.getenv("EMERGENCY_STATE_FILE", "emergency_state.json")
EMERGENCY_COOLDOWN_HOURS = float(os.getenv("EMERGENCY_COOLDOWN_HOURS", "3"))