from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = Flask(__name__)

secret_key = os.getenv("FLASK_SECRET_KEY")

if not secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. "
        "Please configure it in your .env file."
    )

app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # Local HTTP development only
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
)

# Store failed login timestamps for each source IP
failed_attempts = defaultdict(list)

# Store recent security events
security_events = []

# Detection settings
MAX_FAILURES = 5
TIME_WINDOW = 60

DEMO_USERNAME = "student"
DEMO_PASSWORD_HASH = generate_password_hash("Presentation!")

def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login_page"))

        return function(*args, **kwargs)

    return decorated_function

@app.route("/")
@login_required
def home():
    return render_template(
        "dashboard.html",
        username=session.get("username")
    )


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    ip = data.get("ip")
    success = data.get("success")

    if not isinstance(ip, str) or not ip:
        return jsonify({"error": "ip must be a string"}), 400

    if not isinstance(success, bool):
        return jsonify({"error": "success must be a boolean"}), 400

    now = time.time()

    # Remove attempts older than 60 seconds
    failed_attempts[ip] = [
        timestamp
        for timestamp in failed_attempts[ip]
        if now - timestamp < TIME_WINDOW
    ]

    if not success:
        failed_attempts[ip].append(now)

    count = len(failed_attempts[ip])

    alert = not success and count >= MAX_FAILURES

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "success": success,
        "failed_attempts": count,
        "alert": alert
    }

    security_events.append(event)

    # Limit stored events
    if len(security_events) > 100:
        security_events.pop(0)

    return jsonify(event)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()

    response = redirect(url_for("login_page"))
    response.headers["Cache-Control"] = "no-store"

    return response


@app.route("/events")
@login_required
def events():
    return jsonify(security_events)


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/info")
@login_required
def info():
    return jsonify({
        "application": "LoginGuard",
        "pod": os.environ.get("HOSTNAME", "local")
    })

@app.route("/login-page")
def login_page():
    if session.get("authenticated"):
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/authenticate", methods=["POST"])
def authenticate():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # IP of the direct network peer
    client_ip = request.remote_addr

    success = (
        username == DEMO_USERNAME
        and check_password_hash(
            DEMO_PASSWORD_HASH, password
        )
    )

    now = time.time()

    failed_attempts[client_ip] = [
        timestamp
        for timestamp in failed_attempts[client_ip]
        if now - timestamp < TIME_WINDOW
    ]

    if not success:
        failed_attempts[client_ip].append(now)

    count = len(failed_attempts[client_ip])

    alert = not success and count >= MAX_FAILURES

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "ip": client_ip,
        "username": username,
        "success": success,
        "failed_attempts": count,
        "alert": alert
    }

    security_events.append(event)

    if len(security_events) > 100:
        security_events.pop(0)

    if success:
        session.clear()
        session["authenticated"] = True
        session["username"] = username
        session.permanent = True

        return redirect(url_for("home"))

    return render_template(
        "login.html",
        error="Invalid username or password"
    ), 401


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)