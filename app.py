# FILE: app.py
# PURPOSE: Premium subscription web portal and Admin Dashboard for the Weather Alert System.

import os
import csv
import datetime
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from config import (
    CONTACTS_CSV, CITY, OPENWEATHER_API_KEY, GMAIL_ADDRESS, 
    RAINFALL_MM_THRESHOLD, EMERGENCY_WIND_MS, EMERGENCY_TEMP_C
)
from alert import fetch_weather_forecast, send_forecast_to_all
from history_logger import get_alert_history

app = Flask(__name__)
# Secure secret key for sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "weather_secret_key_1262")

# Get admin password (default: admin1262)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1262")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── CSV helper functions ──────────────────────────────────────────────────────

def init_and_upgrade_csv():
    """Ensure contacts.csv has headers (email,name,location,subscribed_at) without breaking existing entries."""
    if not os.path.exists(CONTACTS_CSV):
        # Create parent dir if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(CONTACTS_CSV)), exist_ok=True)
        with open(CONTACTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "name", "location", "subscribed_at"])
        return

    try:
        with open(CONTACTS_CSV, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        
        # If headers are missing or old format (only "email"), upgrade it
        if first_line == "email" or "name" not in first_line:
            logging.info("Upgrading contacts.csv to rich metadata format...")
            emails = []
            with open(CONTACTS_CSV, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    if row and row[0].strip():
                        emails.append(row[0].strip())
            
            with open(CONTACTS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["email", "name", "location", "subscribed_at"])
                for email in emails:
                    writer.writerow([email, "Legacy Subscriber", "Kigali, RW", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")])
            logging.info("Upgrade complete.")
    except Exception as e:
        logging.error("Failed to verify/upgrade CSV: %s", e)

def get_all_contacts() -> list:
    """Returns a list of dictionaries with all contacts."""
    contacts = []
    if not os.path.exists(CONTACTS_CSV):
        return contacts
    try:
        with open(CONTACTS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contacts.append({
                    "email": row.get("email", "").strip(),
                    "name": row.get("name", "N/A").strip(),
                    "location": row.get("location", "Kigali, RW").strip(),
                    "subscribed_at": row.get("subscribed_at", "N/A").strip()
                })
    except Exception as e:
        logging.error("Failed to read contacts: %s", e)
    return contacts

def add_contact_to_csv(email: str, name: str, location: str) -> bool:
    """Adds a new contact to the CSV file, returns True if added, False if duplicate."""
    email = email.lower().strip()
    name = name.strip() or "Anonymous Subscriber"
    location = location.strip() or "Kigali, RW"
    
    contacts = get_all_contacts()
    # Check for duplicates
    for contact in contacts:
        if contact["email"].lower() == email:
            return False

    try:
        with open(CONTACTS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([email, name, location, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")])
        return True
    except Exception as e:
        logging.error("Failed to add contact: %s", e)
        return False

def remove_contact_from_csv(email: str) -> bool:
    """Removes a contact by email, returns True if removed, False otherwise."""
    email = email.lower().strip()
    contacts = get_all_contacts()
    
    found = False
    new_contacts = []
    for contact in contacts:
        if contact["email"].lower() == email:
            found = True
        else:
            new_contacts.append(contact)

    if not found:
        return False

    try:
        with open(CONTACTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "name", "location", "subscribed_at"])
            for c in new_contacts:
                writer.writerow([c["email"], c["name"], c["location"], c["subscribed_at"]])
        return True
    except Exception as e:
        logging.error("Failed to remove contact: %s", e)
        return False

# Ensure CSV is properly upgraded on startup
init_and_upgrade_csv()

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    """Public subscription landing page."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        location = request.form.get("location", "").strip() or "Kigali, RW"

        if not email or "@" not in email:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("index"))

        success = add_contact_to_csv(email, name, location)
        if success:
            flash("🎉 Successfully subscribed! You will now receive automated weather planning alerts.", "success")
        else:
            flash("You are already subscribed to this service!", "info")
        return redirect(url_for("index"))

    return render_template("subscribe.html", city=CITY)

@app.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
    """Public unsubscribe page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Please enter your email address.", "error")
            return redirect(url_for("unsubscribe"))

        removed = remove_contact_from_csv(email)
        if removed:
            flash("😔 You have been unsubscribed from our alerts. We are sorry to see you go!", "success")
        else:
            flash("We couldn't find your email in our subscription list.", "error")
        return redirect(url_for("unsubscribe"))

    return render_template("unsubscribe.html")

# ── Admin Routes ──────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Successfully logged in as Admin.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect admin password.", "error")
            return redirect(url_for("admin_login"))

    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    """Log out admin."""
    session.pop("admin_logged_in", None)
    flash("Successfully logged out.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin")
def admin_dashboard():
    """Admin control dashboard."""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    # Fetch data
    contacts = get_all_contacts()
    history = get_alert_history()
    forecast = fetch_weather_forecast()
    
    # Estimate next run time (top of next hour for Railway Cron)
    now = datetime.datetime.now()
    next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    next_run_str = next_hour.strftime("%Y-%m-%d %H:%M:%S")

    # Counts
    total_subscribers = len(contacts)
    legacy_count = sum(1 for c in contacts if c["name"] == "Legacy Subscriber")
    portal_count = total_subscribers - legacy_count

    return render_template(
        "admin.html",
        contacts=contacts,
        history=history,
        forecast=forecast,
        next_run=next_run_str,
        total_subscribers=total_subscribers,
        legacy_count=legacy_count,
        portal_count=portal_count,
        city=CITY,
        rainfall_threshold=RAINFALL_MM_THRESHOLD,
        wind_threshold=EMERGENCY_WIND_MS,
        temp_threshold=EMERGENCY_TEMP_C
    )

@app.route("/admin/contacts/delete/<email>", methods=["POST"])
def admin_delete_contact(email):
    """Admin action to delete a contact."""
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    removed = remove_contact_from_csv(email)
    if removed:
        return jsonify({"success": True, "message": f"Deleted {email}"})
    return jsonify({"success": False, "message": "Failed to delete"}), 400

@app.route("/admin/contacts/add", methods=["POST"])
def admin_add_contact():
    """Admin action to add a contact manually."""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    name = request.form.get("name", "").strip() or "Added by Admin"
    email = request.form.get("email", "").strip()
    location = request.form.get("location", "").strip() or "Kigali, RW"

    if not email or "@" not in email:
        flash("Invalid email address.", "error")
        return redirect(url_for("admin_dashboard"))

    success = add_contact_to_csv(email, name, location)
    if success:
        flash(f"Successfully added subscriber: {email}", "success")
    else:
        flash("Email is already subscribed.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/trigger-now", methods=["POST"])
def admin_trigger_now():
    """Admin action to manually trigger the full weather alert run immediately."""
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        # Run the full weather check and dispatch to all contacts
        send_forecast_to_all()
        return jsonify({"success": True, "message": "Weather check triggered successfully! Checked live forecast and sent matching updates to all contacts."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error running weather dispatcher: {e}"}), 500

if __name__ == "__main__":
    # In development, run local server. In production, Railway will use gunicorn/Procfile.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
