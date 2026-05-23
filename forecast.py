# FILE: forecast.py
# PURPOSE: Legacy standalone forecast module (predecessor of alert.py).
#          Retained for reference; primary dispatch logic is in alert.py.
#          Twilio has been fully replaced with GmailMessenger (smtplib / email.mime).

import csv
import datetime
import logging

import requests

from alert import GmailMessenger
from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    CITY, OPENWEATHER_API_KEY, CONTACTS_CSV,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_contacts(csv_file: str = CONTACTS_CSV) -> list[str]:
    """Read recipient email addresses from the contacts CSV file."""
    emails = []
    try:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = row.get("email", "").strip()
                if raw:
                    emails.append(raw)
    except FileNotFoundError:
        logging.warning(f"{csv_file} not found. No contacts loaded.")
    return emails


def fetch_weather_forecast() -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {"error": f"API {resp.status_code}: {resp.json().get('message', 'Unknown')}"}
        data = resp.json()
        return {
            "city":      CITY.split(",")[0].title(),
            "condition": data["weather"][0]["description"],
            "temp":      float(data["main"]["temp"]),
            "humidity":  int(data["main"]["humidity"]),
            "wind":      float(data["wind"].get("speed", 0.0)),
        }
    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}


def choose_tips(forecast: dict):
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
    if wind >= 10:
        return "🌬️", ("Gusty winds — secure loose items.", "Be cautious on motorcycles.")
    return "🌈", ("Monitor conditions closely.", "Be prepared for sudden changes.")


def generate_forecast_message() -> str:
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


def send_forecast_to_all():
    body    = generate_forecast_message()
    emails  = load_contacts()
    city    = CITY.split(",")[0].title()
    subject = f"🌦 Weather Update — {city}"

    if not emails:
        logging.warning("No contacts found.")
        return

    messenger = GmailMessenger(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    logging.info("Sending alert to %d recipient(s)...", len(emails))

    for email in emails:
        try:
            messenger.send_email(email, subject, body)
            logging.info("Email sent to %s", email)
        except Exception as e:
            logging.error("Email failed for %s: %s", email, e)

    logging.info("All alerts processed.")