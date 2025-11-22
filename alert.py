# FILE: alert.py
# PURPOSE: Weather forecast → emergency logic → Twilio send (WhatsApp → SMS fallback)

import csv
import datetime
import json
import logging
import os
import requests
from twilio.rest import Client
from typing import Dict

from config import (
    TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER,
    CITY, OPENWEATHER_API_KEY, CONTACTS_CSV,
    RAINFALL_MM_THRESHOLD, EMERGENCY_WIND_MS, EMERGENCY_TEMP_C,
    EMERGENCY_STATE_FILE, EMERGENCY_COOLDOWN_HOURS
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------------- CONTACT HELPERS ----------------

def normalize_number(number: str) -> str:
    n = number.strip().replace(" ", "")
    if not n.startswith("+"):
        if n.startswith("0"):
            n = "+250" + n[1:]
        else:
            n = "+" + n
    return n


def load_contacts(csv_file: str = CONTACTS_CSV) -> list[str]:
    numbers = []
    try:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = row.get("phone_number", "").strip()
                if raw:
                    numbers.append(normalize_number(raw))
    except FileNotFoundError:
        logging.warning(f"{csv_file} not found.")
    return numbers


# ---------------- EMERGENCY STATE ----------------

def load_emergency_state() -> Dict:
    if not os.path.exists(EMERGENCY_STATE_FILE):
        return {}
    try:
        with open(EMERGENCY_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to read state file: {e}")
        return {}


def save_emergency_state(state: Dict):
    try:
        with open(EMERGENCY_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        logging.error(f"Failed to write state file: {e}")


# ---------------- WEATHER FETCH ----------------

def fetch_weather_forecast() -> dict:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            try:
                msg = resp.json().get("message", "Unknown")
            except Exception:
                msg = "Unknown"
            return {"error": f"API {resp.status_code}: {msg}"}
        data = resp.json()

        rain = data.get("rain", {})
        rain_1h = float(rain.get("1h", 0.0))
        rain_3h = float(rain.get("3h", 0.0))

        return {
            "city": CITY.split(",")[0].title(),
            "condition": str(data["weather"][0]["description"]),
            "temp": float(data["main"]["temp"]),
            "humidity": int(data["main"]["humidity"]),
            "wind": float(data.get("wind", {}).get("speed", 0.0)),
            "rain_1h": rain_1h,
            "rain_3h": rain_3h,
        }
    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}


# ---------------- EMERGENCY DECISION ----------------

def should_trigger_emergency(forecast: dict) -> dict:
    if "error" in forecast:
        return {"trigger": False, "reason": "fetch_error", "metric": 0.0}

    if forecast.get("rain_3h", 0.0) >= RAINFALL_MM_THRESHOLD:
        return {"trigger": True, "reason": "heavy_rain_3h", "metric": forecast["rain_3h"]}

    if forecast.get("rain_1h", 0.0) >= RAINFALL_MM_THRESHOLD:
        return {"trigger": True, "reason": "heavy_rain_1h", "metric": forecast["rain_1h"]}

    cond = forecast["condition"].lower()
    if ("storm" in cond or "thunder" in cond) and forecast["wind"] >= (EMERGENCY_WIND_MS * 0.75):
        return {"trigger": True, "reason": "storm_with_wind", "metric": forecast["wind"]}

    if forecast["temp"] >= EMERGENCY_TEMP_C:
        return {"trigger": True, "reason": "extreme_heat", "metric": forecast["temp"]}

    return {"trigger": False, "reason": "none", "metric": 0.0}


# ---------------- MESSAGE GENERATION ----------------

def choose_tips(forecast: dict):
    cond = forecast["condition"].lower()
    temp = forecast["temp"]
    wind = forecast["wind"]

    if "thunder" in cond or "storm" in cond:
        return "🌩️", ("Stay indoors and unplug electronics.", "Avoid tall trees and metal objects.")
    if "rain" in cond:
        return "🌧️", ("Carry umbrella.", "Avoid flooded routes.")
    if "clear" in cond or "sun" in cond:
        if temp >= 30:
            return "☀️", ("High heat risk.", "Hydrate and avoid midday sun.")
        return "☀️", ("Clear skies.", "Enjoy safely.")
    if wind >= 10:
        return "🌬️", ("Secure loose items.", "Be careful on motorcycles.")
    return "🌦️", ("Monitor weather.", "Expect sudden changes.")


def generate_normal_message(forecast: dict) -> str:
    if "error" in forecast:
        return f"⚠️ WEATHER UPDATE ERROR: {forecast['error']}"

    emoji, (tip1, tip2) = choose_tips(forecast)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"🌦 WEATHER UPDATE: {forecast['condition'].capitalize()} in {forecast['city']} {emoji}\n\n"
        f"🌡 Temp: {forecast['temp']:.1f}°C\n"
        f"💧 Humidity: {forecast['humidity']}%\n"
        f"🌬 Wind: {forecast['wind']:.1f} m/s\n"
        f"🕒 Time: {now}\n\n"
        f"🔸 {tip1}\n"
        f"🔸 {tip2}\n\n"
        f"— jean de dieu CST"
    )


def generate_emergency_message(forecast: dict, reason: str, metric: float) -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if reason.startswith("heavy_rain"):
        return (
            f"‼️ EMERGENCY FLOOD ALERT: Heavy rain in {forecast['city']} 🌧️\n\n"
            f"Rain (3h/1h): {forecast['rain_3h']:.1f} / {forecast['rain_1h']:.1f} mm\n"
            f"🕒 {now}\n\n"
            f"Action: Move to higher ground, avoid flooded areas.\n\n"
            f"— JEAN DE DIEU CST"
        )

    if reason == "storm_with_wind":
        return (
            f"‼️ EMERGENCY STORM ALERT in {forecast['city']} 🌩️\n\n"
            f"Wind: {metric:.1f} m/s\n"
            f"Condition: {forecast['condition']}\n"
            f"🕒 {now}\n\n"
            f"Stay indoors and secure loose items.\n\n"
            f"— JEAN DE DIEU CST"
        )

    if reason == "extreme_heat":
        return (
            f"‼️ HEAT EMERGENCY in {forecast['city']} ☀️\n\n"
            f"Temp: {metric:.1f}°C\n"
            f"🕒 {now}\n\n"
            f"Hydrate and limit outdoor activity.\n\n"
            f"— JEAN DE DIEU CST"
        )

    return f"‼️ EMERGENCY ({reason}) — Check local guidance. {now}"


# ---------------- TWILIO MESSENGER ----------------

class TwilioMessenger:
    def __init__(self, sid, token, whatsapp_from, sms_from):
        self.client = Client(sid, token)
        self.whatsapp_from = (
            f"whatsapp:{whatsapp_from}"
            if whatsapp_from and not str(whatsapp_from).startswith("whatsapp:")
            else whatsapp_from
        )
        self.sms_from = sms_from

    def send_whatsapp(self, number, body):
        if not self.whatsapp_from:
            raise ValueError("WhatsApp sender not configured.")

        # Accept LIST or single number
        if isinstance(number, list):
            last_msg = None
            for num in number:
                last_msg = self.client.messages.create(
                    body=body,
                    from_=self.whatsapp_from,
                    to=f"whatsapp:{num}"
                )
            return last_msg

        # Single number case
        return self.client.messages.create(
            body=body,
            from_=self.whatsapp_from,
            to=f"whatsapp:{number}"
        )

    def send_sms(self, number, body):
        if not self.sms_from:
            raise ValueError("SMS sender not configured.")

        # Accept LIST or single number
        if isinstance(number, list):
            last_msg = None
            for num in number:
                last_msg = self.client.messages.create(
                    body=body,
                    from_=self.sms_from,
                    to=num
                )
            return last_msg

        return self.client.messages.create(
            body=body,
            from_=self.sms_from,
            to=number
        )


# ---------------- SEND TO ALL CONTACTS ----------------

def send_forecast_to_all():
    forecast = fetch_weather_forecast()
    numbers = load_contacts()

    if not numbers:
        logging.warning("No contacts found.")
        return

    decision = should_trigger_emergency(forecast)
    state = load_emergency_state()
    now = datetime.datetime.utcnow()

    messenger = TwilioMessenger(TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER)

    if decision["trigger"]:
        last_sent = state.get(decision["reason"])
        cooldown = datetime.timedelta(hours=EMERGENCY_COOLDOWN_HOURS)

        if last_sent:
            try:
                last_time = datetime.datetime.fromisoformat(last_sent)
            except Exception:
                last_time = None
        else:
            last_time = None

        if last_time and (now - last_time) < cooldown:
            logging.info(f"Emergency already sent recently. Sending normal update only.")
            body = generate_normal_message(forecast)
            _send_to_numbers(messenger, numbers, body)
            return

        # Send emergency
        body = generate_emergency_message(forecast, decision["reason"], decision["metric"])
        _send_to_numbers(messenger, numbers, body)

        # Save state
        state[decision["reason"]] = now.isoformat()
        save_emergency_state(state)

    else:
        # Normal update
        body = generate_normal_message(forecast)
        _send_to_numbers(messenger, numbers, body)


def _send_to_numbers(messenger: TwilioMessenger, numbers: list, body: str):
    logging.info(f"Sending message to {len(numbers)} numbers...")
    for number in numbers:
        try:
            msg = messenger.send_whatsapp(number, body)
            logging.info(f"WhatsApp sent to {number}, SID: {msg.sid}")
        except Exception as e:
            logging.warning(f"WhatsApp failed for {number}: {e}. Trying SMS...")
            try:
                msg = messenger.send_sms(number, body)
                logging.info(f"SMS sent to {number}, SID: {msg.sid}")
            except Exception as e2:
                logging.error(f"SMS failed for {number}: {e2}")
