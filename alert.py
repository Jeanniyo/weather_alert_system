# FILE: alert.py
# PURPOSE: Weather forecast → emergency logic → Gmail SMTP delivery (HTML)

import csv
import datetime
import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

import requests

from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
    CITY, OPENWEATHER_API_KEY, CONTACTS_CSV,
    RAINFALL_MM_THRESHOLD, EMERGENCY_WIND_MS, EMERGENCY_TEMP_C,
    EMERGENCY_STATE_FILE, EMERGENCY_COOLDOWN_HOURS,
)
from email_html import build_normal_html, build_emergency_html
from history_logger import log_alert_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------------- CONTACT HELPERS ----------------

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
        logging.warning(f"{csv_file} not found.")
    return emails


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
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
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
            "city":       CITY.split(",")[0].title(),
            "condition":  str(data["weather"][0]["description"]),
            "temp":       float(data["main"]["temp"]),
            "humidity":   int(data["main"]["humidity"]),
            "wind":       float(data.get("wind", {}).get("speed", 0.0)),
            "rain_1h":    rain_1h,
            "rain_3h":    rain_3h,
            "clouds":     int(data.get("clouds", {}).get("all", 0)),
            "visibility": int(data.get("visibility", 10000)) // 1000,
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


def _subject_for_reason(reason: str, city: str) -> str:
    """Build an appropriate email subject line for emergency or normal alerts."""
    labels = {
        "heavy_rain_3h":  f"‼️ FLOOD ALERT — Heavy Rain in {city}",
        "heavy_rain_1h":  f"‼️ FLOOD ALERT — Heavy Rain in {city}",
        "storm_with_wind": f"‼️ STORM ALERT — {city}",
        "extreme_heat":   f"‼️ HEAT EMERGENCY — {city}",
    }
    return labels.get(reason, f"🌦 Weather Update — {city}")


# ---------------- GMAIL MESSENGER ----------------

class GmailMessenger:
    """
    Zero-cost, zero-dependency email dispatcher using smtplib + email.mime.
    Connects to smtp.gmail.com:587 with STARTTLS.

    Prerequisites:
        • GMAIL_ADDRESS    — your Gmail address
        • GMAIL_APP_PASSWORD — 16-char App Password from Google Account > Security
          (NOT your regular password; requires 2-Step Verification enabled)
    """

    def __init__(self, address: str, app_password: str):
        self.address = address
        self.app_password = app_password

    def _validate(self):
        if not self.address or not self.app_password:
            raise ValueError(
                "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in your .env file."
            )

    def send_email(self, to: str, subject: str, body: str,
                   html_body: str | None = None) -> bool:
        """
        Send an email.
        - If html_body is provided → send HTML-only (no plain-text alternative).
          This prevents Gmail from showing a second ugly plain-text version.
        - If no html_body → fall back to plain-text only.
        """
        self._validate()

        if html_body:
            # HTML-only message inside a MIMEMultipart container.
            # This ensures complete MIME-Version: 1.0 headers and correct boundaries,
            # preventing email clients from displaying it as raw plain text,
            # while still excluding any plain-text part to avoid duplicates.
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = self.address
            msg["To"]      = to
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        else:
            # Plain-text fallback (no HTML available)
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = self.address
            msg["To"]      = to
            msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.address, self.app_password)
            smtp.sendmail(self.address, to, msg.as_string())

        return True


def send_forecast_to_all():
    forecast = fetch_weather_forecast()
    emails   = load_contacts()

    if not emails:
        logging.warning("No contacts found in %s.", CONTACTS_CSV)
        return

    decision = should_trigger_emergency(forecast)
    state    = load_emergency_state()
    now      = datetime.datetime.utcnow()
    city     = forecast.get("city", CITY.split(",")[0].title())

    messenger = GmailMessenger(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)

    if decision["trigger"]:
        last_sent = state.get(decision["reason"])
        cooldown  = datetime.timedelta(hours=EMERGENCY_COOLDOWN_HOURS)

        last_time = None
        if last_sent:
            try:
                last_time = datetime.datetime.fromisoformat(last_sent)
            except Exception:
                last_time = None

        if last_time and (now - last_time) < cooldown:
            logging.info("Emergency already sent recently. Sending normal update only.")
            subject   = f"🌦 Weather Update — {city}"
            plain     = generate_normal_message(forecast)
            _, tips   = choose_tips(forecast) if "condition" in forecast else ("🌦", ("Monitor local conditions.", "Stay safe."))
            html      = build_normal_html(forecast, tips) if "condition" in forecast else None
            success, fail, err = _send_emails(messenger, emails, subject, plain, html)
            log_alert_event("NORMAL", subject, success, forecast, "SUCCESS" if not err else "FAILED", err)
            return

        # Send emergency
        subject = _subject_for_reason(decision["reason"], city)
        plain   = generate_emergency_message(forecast, decision["reason"], decision["metric"])
        html    = build_emergency_html(forecast, decision["reason"], decision["metric"])
        success, fail, err = _send_emails(messenger, emails, subject, plain, html)
        log_alert_event("EMERGENCY", subject, success, forecast, "SUCCESS" if not err else "FAILED", err)

        state[decision["reason"]] = now.isoformat()
        save_emergency_state(state)

    else:
        subject = f"🌦 Weather Update — {city}"
        plain   = generate_normal_message(forecast)
        _, tips = choose_tips(forecast) if "condition" in forecast else ("🌦", ("Monitor local conditions.", "Stay safe."))
        html    = build_normal_html(forecast, tips) if "condition" in forecast else None
        success, fail, err = _send_emails(messenger, emails, subject, plain, html)
        log_alert_event("NORMAL", subject, success, forecast, "SUCCESS" if not err else "FAILED", err)


def _send_emails(messenger: GmailMessenger, emails: list, subject: str,
                 body: str, html_body: str | None = None) -> tuple[int, int, str | None]:
    """Sends emails and returns (success_count, fail_count, last_error)."""
    success_count = 0
    fail_count = 0
    last_error = None
    logging.info("Sending email to %d recipient(s)...", len(emails))
    for email in emails:
        try:
            messenger.send_email(email, subject, body, html_body)
            logging.info("Email sent to %s", email)
            success_count += 1
        except smtplib.SMTPAuthenticationError as e:
            last_error = "SMTP authentication failed"
            logging.error(last_error)
            fail_count += len(emails) - success_count
            break
        except Exception as e:
            last_error = str(e)
            logging.error("Email failed for %s: %s", email, e)
            fail_count += 1
    return success_count, fail_count, last_error
