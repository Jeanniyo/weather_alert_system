# FILE: history_logger.py
# PURPOSE: Manage historical logs of sent alerts in a structured JSON file.

import os
import json
import datetime
from config import HISTORY_JSON

def log_alert_event(alert_type: str, subject: str, recipients_count: int, forecast: dict, status: str = "SUCCESS", error: str = None):
    """
    Appends an alert event log to the history.json file.
    """
    event = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alert_type": alert_type, # "NORMAL" or "EMERGENCY"
        "subject": subject,
        "recipients_count": recipients_count,
        "status": status,
        "error": error,
        "city": forecast.get("city", "Kigali"),
        "condition": forecast.get("condition", "N/A"),
        "temp": forecast.get("temp", 0.0),
        "wind": forecast.get("wind", 0.0),
        "rain_1h": forecast.get("rain_1h", 0.0),
        "rain_3h": forecast.get("rain_3h", 0.0)
    }

    history = []
    if os.path.exists(HISTORY_JSON):
        try:
            with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []

    # Keep only the last 200 alerts to avoid file growing indefinitely
    history.insert(0, event)
    history = history[:200]

    try:
        with open(HISTORY_JSON, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        import logging
        logging.error("Failed to write to alert history: %s", e)

def get_alert_history() -> list:
    """
    Returns the list of historical alerts.
    """
    if not os.path.exists(HISTORY_JSON):
        return []
    try:
        with open(HISTORY_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []
