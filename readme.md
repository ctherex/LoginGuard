# 🛡️ LoginGuard

**A Kubernetes-Based Login Security Monitoring System**

LoginGuard is a Python Flask cybersecurity application designed to monitor authentication attempts, detect potential brute-force attacks, and temporarily lock accounts after repeated failed login attempts.

The application uses Redis to store security events, failed-login counters, and account lockout information. This allows multiple Flask instances to share the same security data when deployed across a Kubernetes cluster.

LoginGuard is being developed as a cybersecurity final project demonstrating container orchestration, application self-healing, and worker-node failover using Minikube.

## Features

- **User Authentication:** Login and logout functionality using Flask sessions.
- **Multiple Accounts:** Includes `student` and `admin` demonstration accounts.
- **Brute-Force Detection:** Detects five failed login attempts from the same IP address within 60 seconds.
- **Account Lockouts:** Temporarily locks an account for 60 seconds after five failed login attempts within 60 seconds.
- **Security Event Logging:** Records timestamps, source IP addresses, attempted usernames, authentication results, and security alerts.
- **Security Dashboard:** Displays login statistics, recent events, and currently locked accounts.
- **Redis Integration:** Shares authentication security state across application instances.
- **Health Monitoring:** Provides endpoints for Kubernetes liveness and readiness probes.
- **Session Management:** Restricts access to the dashboard and supports logout.

## Technology Stack

| Technology            | Purpose                                     |
| --------------------- | ------------------------------------------- |
| Python 3              | Application logic                           |
| Flask                 | Web application and authentication          |
| Werkzeug              | Password hashing and verification           |
| Redis                 | Shared security event and lockout storage   |
| Docker                | Application containerization                |
| Kubernetes            | Container orchestration and recovery        |
| Minikube              | Local multi-node Kubernetes environment     |
| HTML, CSS, JavaScript | Security dashboard and login interface      |
| Gunicorn              | Application server for container deployment |

## Project Structure

```text
LoginGuard/
├── app.py
├── storage.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── README.md
│
├── templates/
│   ├── login.html
│   └── dashboard.html
│
├── static/
│   └── style.css
│
└── kubernetes/
    ├── deployment.yaml
    ├── service.yaml
    └── redis.yaml
```

Some container and Kubernetes files may still be under development.

---

# Local Installation

These instructions allow LoginGuard to run on a Linux computer without Kubernetes.

## Prerequisites

Install the following software:

- Python 3.10 or newer
- Python pip and venv
- Docker Engine
- Git

Docker is used to run Redis locally. Minikube and kubectl are only required for Kubernetes deployment.

## 1. Clone the Repository

```bash
git clone https://github.com/ctherex/LoginGuard.git
cd LoginGuard
```

## 2. Create a Python Virtual Environment

On Linux or macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The dependency file should include Flask, Redis, python-dotenv, and Gunicorn, along with any other packages required by the application.

## 4. Configure Environment Variables

Create your local `.env` file:

```bash
cp .env.example .env
```

If `.env.example` is not available yet, create `.env` manually.

Generate a Flask secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Configure `.env`:

```dotenv
FLASK_SECRET_KEY=replace-with-generated-secret-key
REDIS_HOST=localhost
REDIS_PORT=6379
```

Replace the placeholder with your generated key.

The Flask secret key signs authentication session cookies. Keep it private and consistent across application restarts.

**Never commit `.env` to GitHub.**

## 5. Start Redis

LoginGuard requires Redis for shared security event storage and account lockout tracking.

Start Redis using Docker:

```bash
docker run -d \
  --name loginguard-redis \
  -p 127.0.0.1:6379:6379 \
  redis:7-alpine
```

Verify Redis is running:

```bash
docker exec loginguard-redis redis-cli ping
```

Expected response:

```text
PONG
```

If the Redis container already exists but is stopped, start it using:

```bash
docker start loginguard-redis
```

The local Redis container uses temporary storage unless persistence is configured separately.

## 6. Start LoginGuard

Activate the Python virtual environment if it is not already active:

```bash
source venv/bin/activate
```

Start Flask:

```bash
python3 app.py
```

The application should become available at:

[**http://127.0.0.1:5000/login-page**](http://127.0.0.1:5000/login-page)

The Flask development server is intended for local testing only.

---

# Using LoginGuard

## Demonstration Accounts

LoginGuard includes two example accounts:

| Username  | Password           |
| --------- | ------------------ |
| `student` | `StudentDemo2026!` |
| `admin`   | `AdminDemo2026!`   |

These are demonstration-only credentials defined in `app.py`. Verify that they match the values configured in your local copy.

Do not reuse these passwords for any real accounts.

## Login Page

Navigate to:

[http://127.0.0.1:5000/login-page](http://127.0.0.1:5000/login-page)

Enter a valid username and password.

After successful authentication, LoginGuard redirects to the security dashboard.

Invalid login attempts are recorded as security events.

## Security Dashboard

After authentication, navigate to:

[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

The dashboard displays:

- Total recorded login attempts
- Failed login attempts
- Security alerts
- Number of currently locked accounts
- Recent authentication events
- Attempted usernames and source IP addresses
- Remaining account lockout time
- Application instance information

The dashboard automatically refreshes its security information every few seconds.

## Logout

Click **Logout** in the dashboard header.

This clears the authenticated Flask session and redirects to the login page.

Protected dashboard endpoints require authentication.

---

# Security Detection

## Brute-Force Detection

LoginGuard monitors repeated failed login attempts by source IP address.

| Setting             | Value                         |
| ------------------- | ----------------------------- |
| Detection threshold | 5 failures                    |
| Detection window    | 60 seconds                    |
| Detection method    | Source IP address             |
| Alert               | Possible brute-force activity |

When an IP address reaches five failed attempts within the detection window, LoginGuard generates a security alert.

## Account Lockouts

LoginGuard also tracks failed attempts against individual user accounts.

| Setting           | Value              |
| ----------------- | ------------------ |
| Failure threshold | 5                  |
| Failure window    | 60 seconds         |
| Lockout duration  | 60 seconds         |
| Lockout scope     | Individual account |

When an account reaches five failed attempts, it becomes temporarily locked.

During the lockout, authentication is rejected even if the correct password is supplied.

After 60 seconds, Redis automatically expires the lockout key and the account becomes available again.

A successful login clears the account's previous failed-attempt history.

## Testing Account Lockouts

1. Start Redis and LoginGuard.
2. Log in as `student` and open the dashboard.
3. Open a separate private browser window.
4. Attempt to log in as `admin` with an incorrect password five times within 60 seconds.
5. Verify that the fifth attempt triggers an account lockout.
6. Confirm that the dashboard displays `admin` under Currently Locked Accounts.
7. Try the correct `admin` password during the lockout.
8. Wait 60 seconds and verify that the account becomes available again.

The `student` account should remain accessible while `admin` is locked.

---

# Redis Integration

LoginGuard uses Redis instead of Python dictionaries to store shared security information.

## Redis Data Structures

| Data                             | Redis structure |
| -------------------------------- | --------------- |
| Failed login attempts by IP      | Sorted set      |
| Failed login attempts by account | Sorted set      |
| Account lockout status           | Expiring key    |
| Recent security events           | List            |

Redis provides a shared state that multiple LoginGuard instances can access simultaneously.

This is necessary for Kubernetes because each application replica runs in its own container.

## Inspecting Redis

Open the Redis CLI:

```bash
docker exec -it loginguard-redis redis-cli
```

List LoginGuard keys using:

```redis
SCAN 0 MATCH loginguard:*
```

Check the remaining lockout duration for `admin`:

```redis
TTL loginguard:lockout:admin
```

View recent security events:

```redis
LRANGE loginguard:events 0 9
```

The Redis TTL command returns the remaining number of seconds before a key expires.

## Redis Availability

If Redis becomes unavailable, LoginGuard's authentication system should reject requests rather than bypassing security checks.

The application provides a readiness endpoint that checks Redis connectivity.

Redis is currently configured as a single instance. A production deployment would require additional planning for persistence, authentication, and Redis high availability.

---

# Health and Readiness Endpoints

LoginGuard provides two endpoints for Kubernetes.

| Endpoint      | Purpose                   | Expected response                |
| ------------- | ------------------------- | -------------------------------- |
| `GET /health` | Flask process health      | HTTP 200                         |
| `GET /ready`  | Flask and Redis readiness | HTTP 200 when Redis is available |

Test locally:

```bash
curl http://localhost:5000/health
```

```bash
curl http://localhost:5000/ready
```

When Redis is unavailable, `/ready` should return HTTP 503.

Kubernetes should use `/health` for liveness checks and `/ready` for readiness checks.

---

# Docker Deployment

LoginGuard can be packaged as a Docker container.

Once the Dockerfile is configured, build the image:

```bash
docker build -t loginguard:1.0 .
```

For a local Docker deployment, Redis must be reachable from the application container.

The hostname `localhost` inside a container refers to that container, not the Linux host or another container.

A Docker network can be used to connect LoginGuard and Redis:

```bash
docker network create loginguard-network
```

For a fresh Redis container attached to that network:

```bash
docker run -d \
  --name loginguard-redis \
  --network loginguard-network \
  redis:7-alpine
```

If a container with that name already exists, stop and remove it or connect the existing container to the network instead.

Run LoginGuard:

```bash
docker run --rm \
  --network loginguard-network \
  -p 127.0.0.1:5000:5000 \
  --env-file .env \
  -e REDIS_HOST=loginguard-redis \
  loginguard:1.0
```

The image should start Gunicorn listening on `0.0.0.0:5000`.

The application will be accessible at:

[http://127.0.0.1:5000/login-page](http://127.0.0.1:5000/login-page)

---

# Kubernetes Deployment

LoginGuard is intended to run on a three-node Minikube cluster.

## Cluster Architecture

```text
                  Linux Laptop
                       |
                Local Application URL
                       |
              Kubernetes Service
                       |
             +---------+---------+
             |                   |
       Worker Node 1       Worker Node 2
             |                   |
       LoginGuard Pod A    LoginGuard Pod B
             |                   |
             +---------+---------+
                       |
                 Redis Service
                       |
                   Redis Pod

              Kubernetes Control Plane
         Scheduling, health, and recovery
```

## Cluster Requirements

- One Kubernetes control-plane node
- Two worker nodes
- Two LoginGuard replicas
- Redis accessible to both replicas
- Kubernetes Service for application traffic
- Liveness and readiness probes
- Replica placement across separate worker nodes

## Starting Minikube

Install Minikube, kubectl, and Docker.

Start a three-node cluster:

```bash
minikube start --nodes=3 --driver=docker
```

Verify:

```bash
kubectl get nodes -o wide
```

## Deploying Redis

Deploy the Redis resources:

```bash
kubectl apply -f kubernetes/redis.yaml
```

Verify:

```bash
kubectl get pods -l app=redis
kubectl get service redis
```

For the classroom worker-node failover demonstration, Redis can be placed on the control-plane node so that stopping either worker does not stop the shared database.

This is a lab-specific arrangement, not a production high-availability configuration.

## Configuring the Flask Secret Key

Both LoginGuard replicas must use the same Flask secret key.

Create a Kubernetes Secret:

```bash
kubectl create secret generic loginguard-secret \
  --from-literal=FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

The LoginGuard Deployment should load this value through a Secret reference.

Do not regenerate the key every time the application is restarted.

## Connecting LoginGuard to Redis

Configure the application containers with:

```yaml
env:
  - name: REDIS_HOST
    value: redis
  - name: REDIS_PORT
    value: "6379"
  - name: FLASK_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: loginguard-secret
        key: FLASK_SECRET_KEY
```

Both LoginGuard replicas should receive the same configuration.

## Deploying LoginGuard

Build the image:

```bash
docker build -t loginguard:1.0 .
```

Load it into Minikube:

```bash
minikube image load loginguard:1.0
```

Deploy the application:

```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

Verify:

```bash
kubectl get pods -o wide
kubectl get deployments
kubectl get services
```

The two LoginGuard replicas should be running on separate worker nodes.

## Accessing the Application

For initial development:

```bash
kubectl port-forward service/loginguard-service 8080:80
```

Open:

[http://localhost:8080/login-page](http://localhost:8080/login-page)

Port forwarding is suitable for testing, but it may disconnect when the selected pod fails.

For the final failover demonstration, configure a stable local ingress or proxy that can continue routing requests to healthy replicas.

---

# Kubernetes Recovery Demonstrations

## 1. Container Auto-Restart

Terminate an application container's main process in a controlled test.

Verify that Kubernetes restarts the container and increments its restart count.

```bash
kubectl get pods -w
```

## 2. Pod Replacement

Delete a LoginGuard pod:

```bash
kubectl delete pod <pod-name>
```

The Deployment controller should create a replacement pod.

## 3. Worker-Node Failover

Verify the application replicas are on separate nodes:

```bash
kubectl get pods -o wide
```

Stop one worker:

```bash
minikube node stop minikube-m02
```

Confirm that the surviving LoginGuard replica remains accessible and can communicate with Redis.

Restart the worker:

```bash
minikube node start minikube-m02
```

The cluster should recover as Kubernetes reconciles the desired state.

Strict pod anti-affinity may prevent the replacement replica from running on the surviving worker until the failed worker returns.

## 4. Shared Security State

Generate failed login attempts, then direct requests to different application replicas.

Both replicas should observe the same Redis-backed events and account lockout state.

This demonstrates that the security monitoring system works across multiple application instances.

---

# Troubleshooting

## Missing Python Dependencies

Activate the virtual environment:

```bash
source venv/bin/activate
```

Reinstall dependencies:

```bash
pip install -r requirements.txt
```

## Missing Flask Secret Key

Verify that `.env` exists and contains `FLASK_SECRET_KEY`.

Also confirm that `app.py` calls `load_dotenv()` before loading application configuration and importing `storage.py`.

## Redis Connection Refused

Verify Redis is running:

```bash
docker ps
```

Check connectivity:

```bash
docker exec loginguard-redis redis-cli ping
```

Verify `REDIS_HOST` and `REDIS_PORT` in `.env`.

## Redis Container Already Exists

If the Redis container is stopped:

```bash
docker start loginguard-redis
```

If it is already running, do not create a second container with the same name.

## Dashboard Returns HTTP 500

Check the Flask terminal for the Python traceback.

Verify that the HTML templates exist and Redis is reachable.

## Login Sessions Fail Between Replicas

Ensure both replicas use the same `FLASK_SECRET_KEY`.

Different keys cause session cookies signed by one replica to be rejected by another.

## Account Lockout Is Not Shared

Verify that both application replicas connect to the same Redis Service.

Check that the application is no longer using in-memory dictionaries for lockout tracking.

## Kubernetes Pods Are Not Ready

Check:

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

Verify that Redis is running and that `/ready` responds successfully.

---

# Security Considerations

LoginGuard is intended for educational use in a controlled cybersecurity lab.

- Demonstration passwords are not suitable for production.
- Submitted passwords must never be stored in event logs.
- Flask session keys must remain private.
- The security dashboard requires authentication.
- Redis should not be exposed to untrusted networks.
- The Flask development server should not be publicly exposed.
- Use HTTPS and secure session cookies for deployments outside a trusted lab.
- Account lockouts can be abused to deny legitimate users access.
- Reverse proxies may affect client IP logging.
- The current Redis deployment is not highly available.
- Authentication and lockout operations require additional concurrency hardening for production use.

## Development Responsibilities

**Application development**

- Flask authentication
- Security event detection
- Account lockout logic
- Redis integration
- Security dashboard

**Kubernetes development**

- Minikube cluster configuration
- Docker image deployment
- Kubernetes Deployments and Services
- Kubernetes Secrets
- Redis deployment
- Health probes
- Worker-node failover demonstration

## Project Status

LoginGuard is being developed in stages:

- [x] Flask application
- [x] Login and logout functionality
- [x] Multiple demonstration accounts
- [x] Failed-login detection
- [x] Account lockout functionality
- [x] Security dashboard
- [x] Redis integration fully tested
- [ ] Docker deployment verified
- [ ] Multi-node Minikube deployment verified
- [ ] Worker-node failover demonstrated

## License

LoginGuard is an educational project. No specific open-source license has been assigned yet.
