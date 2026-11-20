# LoginGuard

A Python Flask-based cybersecurity application that monitors login attempts, detects potential brute-force attacks, and displays security events through a web dashboard.

LoginGuard is being developed as a cybersecurity final project for deployment on a multi-node Kubernetes cluster using Minikube.

## Features

- User authentication with Flask sessions
- Login and logout functionality
- Failed-login attempt monitoring
- Brute-force detection after 5 failed attempts within 60 seconds
- Source IP address and attempted username logging
- Security event dashboard
- Application health endpoint for Kubernetes
- Planned multi-node deployment and automatic recovery

## Requirements

Before running LoginGuard, install:

- Python 3.10 or newer
- pip
- Python virtual environment support (`venv`)
- Git (optional, for cloning the repository)

Docker, Minikube, and kubectl are not required to run the application locally.

## Installation

### 1. Download the project

Clone the repository:

```bash
git clone <repository-url>
cd loginguard
```

Alternatively, copy the entire project folder onto the computer.

### 2. Create a virtual environment

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses Flask for its web application and `python-dotenv` for local environment configuration.

### 4. Configure the Flask secret key

LoginGuard requires a secret key to sign authentication session cookies.

Generate a random secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Create a file named `.env` in the project root:

```env
FLASK_SECRET_KEY=paste-your-generated-key-here
```

Replace the placeholder with the generated value.

**Important:** Do not commit `.env` to Git or share your secret key publicly.

The application expects `app.py` to load the `.env` file using `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

### 5. Start LoginGuard

From the project directory, with your virtual environment activated:

```bash
python app.py
```

On Linux, you may need:

```bash
python3 app.py
```

By default, the application runs at:

**http://127.0.0.1:5000**

## Using LoginGuard

### Login page

Open:

http://127.0.0.1:5000/login-page

Enter the demonstration account credentials configured in `app.py`.

Successful authentication redirects you to the security dashboard.

Invalid credentials generate failed-login events.

### Security dashboard

After logging in, open:

http://127.0.0.1:5000/

The dashboard displays:

- Total recorded login attempts
- Failed login attempts
- Security alerts
- Recent authentication activity
- Attempted usernames
- Source IP addresses
- Application instance information

The dashboard refreshes its event data automatically.

### Logout

Click **Logout** in the dashboard header.

This clears the authentication session and redirects you to the login page.

Protected dashboard pages require authentication before they can be accessed again.

## Brute-Force Detection

LoginGuard monitors repeated failed authentication attempts.

The default detection settings are:

| Setting | Value |
|---|---|
| Failure threshold | 5 attempts |
| Detection window | 60 seconds |
| Detection grouping | Source IP address |
| Alert type | Possible brute-force attack |

To test detection:

1. Open the login page.
2. Enter an incorrect password.
3. Repeat the failed login five times within 60 seconds.
4. Log in with the valid demonstration credentials.
5. Open the dashboard and review the recorded events.

The fifth failed attempt should generate a security alert.

## Project Structure

```text
loginguard/
├── app.py
├── requirements.txt
├── .env                 # Local configuration (not committed)
├── .gitignore
├── .dockerignore
├── Dockerfile           # Container deployment
├── templates/
│   ├── login.html
│   └── dashboard.html
├── static/
│   └── style.css
└── kubernetes/
    ├── deployment.yaml
    ├── service.yaml
    └── redis.yaml
```

Some container and Kubernetes files may not exist until those stages of the project are implemented.

## Security Notes

LoginGuard is intended for cybersecurity education and controlled laboratory environments.

- Never use real passwords when testing the application.
- Do not store submitted passwords in security event logs.
- Keep the Flask secret key private.
- Use a separate secret key for each independent installation.
- Do not expose Flask's development server directly to the public internet.
- The current in-memory event storage is not persistent.
- Session cookies should use HTTPS-only settings when deployed behind HTTPS.
- Reverse proxies may affect which client IP address Flask observes.

## Troubleshooting

### ModuleNotFoundError

If Python cannot find Flask or another dependency, activate the virtual environment and reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Missing FLASK_SECRET_KEY

Verify that `.env` exists in the project root and contains:

```env
FLASK_SECRET_KEY=your-secret-key
```

Also verify that `app.py` calls `load_dotenv()` before reading the environment variable.

### TemplateNotFound

Verify that `login.html` and `dashboard.html` are inside the `templates/` directory next to `app.py`.

### HTTP 404 Not Found

Check that the Flask route exists in `app.py`.

To list registered routes:

```bash
flask --app app routes
```

### Port 5000 Already in Use

Another process may already be using port 5000.

Stop the existing Flask process or configure the application to use a different port.

### Login Session Not Working

Verify that `FLASK_SECRET_KEY` is configured and remains unchanged between application restarts.

Changing the key invalidates existing signed session cookies.

## Kubernetes Deployment (Planned)

LoginGuard is designed to eventually run on a local Minikube cluster containing:

- 1 Kubernetes control-plane node
- 2 Kubernetes worker nodes
- 2 LoginGuard application replicas
- Shared Redis storage for security events

The Kubernetes deployment will demonstrate:

- Container auto-restart
- Pod replacement
- Load balancing
- Worker-node failover
- Continued application availability

These features require additional containerization and Kubernetes configuration and are not part of the basic local installation.

## Project Status

**Current phase:** Local Flask application development and authentication testing.

**Next phase:** Containerization, shared Redis storage, and multi-node Minikube deployment.

## License

For educational use. Add a license file if the project will be distributed publicly.