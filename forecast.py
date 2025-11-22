import datetime
import logging
import requests
from twilio.rest import Client
from config import (
    TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER,
    CITY, OPENWEATHER_API_KEY, CONTACTS_CSV
)
import csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def load_contacts(csv_file=CONTACTS_CSV):
    numbers = []
    try:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = row.get("phone_number", "").strip()
                if raw:
                    numbers.append(normalize_number(raw))
    except FileNotFoundError:
        logging.warning(f"{csv_file} not found. No numbers loaded.")
    return numbers

def normalize_number(number):
    n = number.strip().replace(" ", "")
    if not n.startswith("+"):
        if n.startswith("0"):
            n = "+250" + n[1:]  # adapt per your contact format
        else:
            n = "+" + n
    return n

def fetch_weather_forecast():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {"error": f"API {resp.status_code}: {resp.json().get('message', 'Unknown')}"}
        data = resp.json()
        return {
            "city": CITY.split(",")[0].title(),
            "condition": data["weather"][0]["description"],  # e.g. "light rain"
            "temp": float(data["main"]["temp"]),
            "humidity": int(data["main"]["humidity"]),
            "wind": float(data["wind"].get("speed", 0.0)),   # m/s
        }
    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}

def choose_tips(forecast):
    cond = forecast["condition"].lower()
    temp = forecast["temp"]
    wind = forecast["wind"]

    if "thunder" in cond or "storm" in cond:
        return "🌩️", ("Stay indoors and unplug electronics.", "Avoid tall trees and metal objects.")
    if "rain" in cond:
        return "🌧️", ("Carry an umbrella and waterproof gear.", "Avoid flood-prone routes.")
    if "drizzle" in cond or "shower" in cond:
        return "🌦️", ("Light rain expected.", "Roads may be slippery.")
    if "snow" in cond:
        return "❄️", ("Bundle up and watch for ice.", "Allow extra travel time.")
    if "clear" in cond or "sun" in cond:
        tips = ["Enjoy the clear skies!", "Stay hydrated."]
        if temp >= 30:
            tips[1] = "Heat risk — limit midday sun exposure."
        return "☀️", tuple(tips)
    if "cloud" in cond or "overcast" in cond:
        return "☁️", ("Carry an umbrella just in case.", "Weather may change suddenly.")
    # Wind-specific tip
    if wind >= 10:  # ~36 km/h
        return "🌬️", ("Gusty winds — secure loose items.", "Be cautious on motorcycles.")
    return "🌈", ("Monitor conditions closely.", "Be prepared for sudden changes.")

def generate_forecast_message():
    forecast = fetch_weather_forecast()
    if "error" in forecast:
        return f"⚠️ WEATHER ALERT ERROR: {forecast['error']}"

    emoji, (tip1, tip2) = choose_tips(forecast)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"⚠️ WEATHER ALERT: {forecast['condition'].capitalize()} in {forecast['city']} {emoji}\n\n"
        f"🌡 Temperature: {forecast['temp']:.1f}°C\n"
        f"💧 Humidity: {forecast['humidity']}%\n"
        f"🌬 Wind: {forecast['wind']:.1f} m/s\n"
        f"🕒 Time: {now}\n\n"
        f"🔸 {tip1}\n"
        f"🔸 {tip2}\n\n"
        f"— jean de dieu CST"
    )

class TwilioMessenger:
    def __init__(self, sid, token, whatsapp_from, sms_from):
        self.client = Client(sid, token)
        self.whatsapp_from = f"whatsapp:{whatsapp_from}" if not str(whatsapp_from).startswith("whatsapp:") else whatsapp_from
        self.sms_from = sms_from

    def send_whatsapp(self, number, body):
        return self.client.messages.create(body=body, from_=self.whatsapp_from, to=f"whatsapp:{number}")

    def send_sms(self, number, body):
        return self.client.messages.create(body=body, from_=self.sms_from, to=number)

def send_forecast_to_all():
    body = generate_forecast_message()
    numbers = load_contacts()
    if not numbers:
        logging.warning("No contacts found.")
        return

    messenger = TwilioMessenger(TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER)
    logging.info(f"Sending alert to {len(numbers)} recipients...")

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

    logging.info("All alerts processed.")