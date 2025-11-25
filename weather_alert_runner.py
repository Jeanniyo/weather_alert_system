import logging
from alert import send_forecast_to_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def main():
    logging.info("Weather alert runner started (Render Cron Job).")
    try:
        send_forecast_to_all()
        logging.info("Weather alert runner completed successfully.")
    except Exception as e:
        logging.exception("Runner failed: %s", e)

if __name__ == "__main__":
    main()
