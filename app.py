from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import time
import redis
import storage

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

USERS = {
    "student": generate_password_hash("Presentation!"),
    "admin": generate_password_hash("admin")
}

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
    try:
        return jsonify(storage.get_events())
    except redis.RedisError:
        return jsonify({
            "error": "Security events unavailable"
        }), 503


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "LoginGuard"
    })

@app.route("/ready")
def ready():
    try:
        if storage.redis_healthy():
            return jsonify({
                "status": "ready",
                "redis": "connected"
            })

    except redis.RedisError:
        pass

    return jsonify({
        "status": "not ready",
        "redis": "unavailable"
    }), 503

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
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    client_ip = request.remote_addr or "unknown"

    # Use the existing demo accounts from USERS.
    # Do not record submitted passwords.

    try:
        # Check lockout before validating the password.
        remaining = (
            storage.get_lockout_remaining(username)
            if username in USERS else 0
        )

        if remaining > 0:
            event = {
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "ip": client_ip,
                "username": username,
                "success": False,
                "failed_attempts": 0,
                "alert": True,
                "event_type": "ACCOUNT_LOCKED"
            }

            storage.save_event(event)

            return render_template(
                "login.html",
                error=(
                    "Account temporarily locked. "
                    f"Try again in {remaining} seconds."
                )
            ), 429

        # Verify credentials.
        success = (
            username in USERS
            and check_password_hash(
                USERS[username], password
            )
        )

        account_locked = False
        account_failure_count = 0

        if success:
            storage.reset_account_failures(username)
            ip_count = storage.get_ip_failure_count(client_ip)

        else:
            ip_count = storage.record_ip_failure(client_ip)

            if username in USERS:
                result = storage.record_account_failure(
                    username
                )

                account_failure_count = result["count"]
                account_locked = result["locked"]

        alert = (
            not success
            and (
                ip_count >= storage.MAX_FAILURES
                or account_locked
            )
        )

        event_type = (
            "LOGIN_SUCCESS" if success
            else "ACCOUNT_LOCKOUT" if account_locked
            else "LOGIN_FAILURE"
        )

        event = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "ip": client_ip,
            "username": username,
            "success": success,
            "failed_attempts": ip_count,
            "account_failures": account_failure_count,
            "account_locked": account_locked,
            "alert": alert,
            "event_type": event_type
        }

        storage.save_event(event)

    except redis.RedisError:
        app.logger.exception("Redis unavailable")

        return render_template(
            "login.html",
            error="Authentication temporarily unavailable."
        ), 503

    if success:
        session.clear()
        session["authenticated"] = True
        session["username"] = username
        session.permanent = True

        return redirect(url_for("home"))

    if account_locked:
        return render_template(
            "login.html",
            error=(
                "Too many failed attempts. "
                "Account locked for 60 seconds."
            )
        ), 429

    return render_template(
        "login.html",
        error="Invalid username or password"
    ), 401

@app.route("/locked-accounts")
@login_required
def get_locked_accounts():
    try:
        accounts = storage.get_locked_accounts(USERS.keys())

        return jsonify({
            "count": len(accounts),
            "accounts": accounts
        })

    except redis.RedisError:
        return jsonify({
            "error": "Lockout information unavailable"
        }), 503

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)