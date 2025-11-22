# FILE: test_send_one.py
# PURPOSE: Test sending one alert message to several numbers
# Algorithm same: WhatsApp → SMS fallback, only error fixed.

from alert import (
    fetch_weather_forecast,
    generate_normal_message,
    TwilioMessenger
)

from config import (
    TWILIO_SID, TWILIO_TOKEN,
    TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER
)

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TARGET_NUMBER = [
    "+250791117367",
    "+250798908094",
    "+250733191077"
]


def send_one():
    forecast = fetch_weather_forecast()
    body = generate_normal_message(forecast)

    messenger = TwilioMessenger(
        TWILIO_SID, TWILIO_TOKEN,
        TWILIO_WHATSAPP_NUMBER, TWILIO_NUMBER
    )

    try:
        msg = messenger.send_whatsapp(TARGET_NUMBER, body)
        logging.info("WhatsApp sent. Last SID: %s", getattr(msg, "sid", "unknown"))
    except Exception as e:
        logging.warning("WhatsApp failed: %s. Trying SMS...", e)
        try:
            msg = messenger.send_sms(TARGET_NUMBER, body)
            logging.info("SMS sent. Last SID: %s", getattr(msg, "sid", "unknown"))
        except Exception as e2:
            logging.error("SMS fallback failed: %s", e2)


if __name__ == "__main__":
    send_one()
