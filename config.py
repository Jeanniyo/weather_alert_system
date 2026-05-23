# FILE: config.py
# PURPOSE: Central configuration loaded from environment variables via python-dotenv

import os
from dotenv import load_dotenv

# Load .env from the project folder
load_dotenv()

# ===== OpenWeather settings =====
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CITY = os.getenv("CITY", "Kigali,RW")

# ===== Gmail SMTP (replaces Twilio) =====
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# ===== Alert thresholds =====
RAIN_POP_THRESHOLD    = float(os.getenv("RAIN_POP_THRESHOLD", "0.6"))
RAINFALL_MM_THRESHOLD = float(os.getenv("RAINFALL_MM_THRESHOLD", "10.0"))

# ===== Data directory & Persistence =====
# On Railway, you can mount a persistent volume at /app/data to preserve subscribers/history.
DATA_DIR = os.getenv("DATA_DIR", ".")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# ===== Default contacts CSV path =====
CONTACTS_CSV = os.path.join(DATA_DIR, os.getenv("CONTACTS_CSV", "contacts.csv"))

# ===== Emergency thresholds and state =====
EMERGENCY_WIND_MS        = float(os.getenv("EMERGENCY_WIND_MS", "12.0"))
EMERGENCY_TEMP_C         = float(os.getenv("EMERGENCY_TEMP_C", "40.0"))
EMERGENCY_STATE_FILE     = os.path.join(DATA_DIR, os.getenv("EMERGENCY_STATE_FILE", "emergency_state.json"))
EMERGENCY_COOLDOWN_HOURS = float(os.getenv("EMERGENCY_COOLDOWN_HOURS", "3"))

# ===== Alert History File =====
HISTORY_JSON = os.path.join(DATA_DIR, "history.json")