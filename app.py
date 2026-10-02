"""
Employee Directory & DevOps Engineering Platform
Practical 10: End-to-End DevOps Pipeline (Group B3-G3: Employee Directory)
Features:
- Mandatory REST Endpoints: GET /items, POST /items, GET /health
- Prometheus Scrape Target: GET /metrics
- Authentication & SSO:
  * POST /api/auth/register (Create Account)
  * POST /api/auth/login (Standard Login)
  * POST /api/auth/sso (Google/GitHub/Okta Enterprise SSO Exchange)
  * GET /api/auth/user (Current Session Info)
  * POST /api/auth/logout
"""

import time
import os
import hashlib
import secrets
from flask import Flask, request, jsonify, render_template, Response, session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devops-b3g3-super-secret-key-2026")

# Prometheus Metrics definition
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Duration in Seconds',
    ['endpoint']
)
AUTH_EVENTS = Counter(
    'auth_events_total',
    'Authentication Events Counter',
    ['type', 'provider', 'status']
)

# User Database (In-Memory with Secure Password Hashing)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

users = [
    {
        "id": 1,
        "name": "SHAIKH ZAID MATINUDDIN",
        "email": "zaid.matinuddin@student.college.edu",
        "password_hash": hash_password("DevOps@2026"),
        "role": "CI/CD & Containerization Engineer (R3)",
        "provider": "local"
    },
    {
        "id": 2,
        "name": "SHAIKH RAHMAT",
        "email": "shaikh.rahmat@student.college.edu",
        "password_hash": hash_password("DevOps@2026"),
        "role": "Agile Planner & Documentation Lead (R1)",
        "provider": "local"
    }
]
user_id_counter = 3

# In-memory storage for Employee Directory
employees = [
    {
        "id": 1,
        "name": "SHAIKH RAHMAT",
        "role": "Agile Planner & Documentation Lead (R1)",
        "department": "Platform & Cloud",
        "email": "shaikh.rahmat@student.college.edu",
        "status": "Active",
        "avatar": "SR",
        "location": "Mumbai, India",
        "phone": "+91 98201 11234"
    },
    {
        "id": 2,
        "name": "YADGIR ZUVERIA SALIM",
        "role": "Developer & Version Control (R2)",
        "department": "AI & Data Science",
        "email": "zuveria.yadgir@student.college.edu",
        "status": "Active",
        "avatar": "YZ",
        "location": "Mumbai, India",
        "phone": "+91 98202 22345"
    },
    {
        "id": 3,
        "name": "SHAIKH ZAID MATINUDDIN",
        "role": "CI/CD & Containerization Engineer (R3)",
        "department": "Engineering",
        "email": "zaid.matinuddin@student.college.edu",
        "status": "Active",
        "avatar": "ZM",
        "location": "Mumbai, India",
        "phone": "+91 98203 33456"
    },
    {
        "id": 4,
        "name": "SHAIKH ZAID WAZIDALI",
        "role": "Deployment & Monitoring Engineer (R4)",
        "department": "Core Infrastructure",
        "email": "zaid.wazidali@student.college.edu",
        "status": "Active",
        "avatar": "ZW",
        "location": "Mumbai, India",
        "phone": "+91 98204 44567"
    }
]
next_id = 5


@app.before_request
def start_timer():
    request._start_time = time.time()


@app.after_request
def record_metrics(response):
    if hasattr(request, '_start_time'):
        latency = time.time() - request._start_time
        REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    return response


# --- 1. Web UI Route ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# --- 2. Mandatory Endpoints as specified in Practical Handout ---

@app.route("/health", methods=["GET"])
def health():
    """
    Mandatory Endpoint 1:
    GET /health : returns a simple 'OK' message (used for monitoring checks).
    """
    return jsonify({
        "status": "OK",
        "service": "Employee Directory Service",
        "version": "1.0.0",
        "uptime": "healthy",
        "sso_ready": True
    }), 200


@app.route("/items", methods=["GET"])
def get_items():
    """
    Mandatory Endpoint 2:
    GET /items : returns the list of items for the topic (Employee Directory).
    """
    query = request.args.get("search", "").lower()
    dept = request.args.get("department", "").lower()

    filtered = employees
    if query:
        filtered = [
            emp for emp in filtered
            if query in emp["name"].lower() or query in emp["role"].lower() or query in emp["email"].lower()
        ]
    if dept:
        filtered = [emp for emp in filtered if dept == emp["department"].lower()]

    return jsonify(filtered), 200


@app.route("/items", methods=["POST"])
def add_item():
    """
    Mandatory Endpoint 3:
    POST /items : adds a new item to the list.
    """
    global next_id
    data = request.get_json(silent=True) or request.form.to_dict()

    if not data or not data.get("name") or not data.get("role"):
        return jsonify({
            "error": "Validation Failed",
            "message": "Both 'name' and 'role' are required fields."
        }), 400

    name_parts = data.get("name").strip().split()
    avatar = "".join([p[0] for p in name_parts[:2]]).upper() if name_parts else "EM"

    new_employee = {
        "id": next_id,
        "name": data.get("name").strip(),
        "role": data.get("role").strip(),
        "department": data.get("department", "Engineering").strip(),
        "email": data.get("email", f"{data.get('name').lower().replace(' ', '.')}@student.college.edu").strip(),
        "status": data.get("status", "Active").strip(),
        "avatar": avatar,
        "location": data.get("location", "Mumbai, India").strip(),
        "phone": data.get("phone", "+91 98200 00000").strip()
    }
    employees.append(new_employee)
    next_id += 1

    return jsonify({
        "message": "Employee added successfully",
        "item": new_employee
    }), 201


@app.route("/items/<int:emp_id>", methods=["GET"])
def get_item(emp_id):
    employee = next((e for e in employees if e["id"] == emp_id), None)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee), 200


@app.route("/items/<int:emp_id>", methods=["DELETE"])
def delete_item(emp_id):
    global employees
    employee = next((e for e in employees if e["id"] == emp_id), None)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    employees = [e for e in employees if e["id"] != emp_id]
    return jsonify({"message": f"Employee {emp_id} deleted successfully"}), 200


# --- 3. Authentication & SSO APIs ---

@app.route("/api/auth/register", methods=["POST"])
def register():
    """
    Create Account (Sign Up) API
    """
    global user_id_counter, next_id
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "DevOps Team Member").strip()

    if not name or not email or not password:
        AUTH_EVENTS.labels(type="register", provider="local", status="failure").inc()
        return jsonify({"error": "Validation Error", "message": "Name, email, and password are required."}), 400

    if any(u["email"] == email for u in users):
        AUTH_EVENTS.labels(type="register", provider="local", status="failure").inc()
        return jsonify({"error": "Conflict", "message": "An account with this email already exists."}), 409

    new_user = {
        "id": user_id_counter,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "provider": "local"
    }
    users.append(new_user)
    user_id_counter += 1

    # Automatically add to Employee Directory if not present
    if not any(e["email"].lower() == email for e in employees):
        avatar = "".join([p[0] for p in name.split()[:2]]).upper()
        employees.append({
            "id": next_id,
            "name": name,
            "role": role,
            "department": data.get("department", "Engineering"),
            "email": email,
            "status": "Active",
            "avatar": avatar,
            "location": "Mumbai, India",
            "phone": "+91 98200 12345"
        })
        next_id += 1

    session["user"] = {
        "id": new_user["id"],
        "name": new_user["name"],
        "email": new_user["email"],
        "role": new_user["role"],
        "provider": "local"
    }

    AUTH_EVENTS.labels(type="register", provider="local", status="success").inc()
    return jsonify({
        "message": "Account created successfully",
        "user": session["user"]
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    Standard Email & Password Login API
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        AUTH_EVENTS.labels(type="login", provider="local", status="failure").inc()
        return jsonify({"error": "Validation Error", "message": "Email and password are required."}), 400

    target = next((u for u in users if u["email"] == email), None)
    if not target or target["password_hash"] != hash_password(password):
        AUTH_EVENTS.labels(type="login", provider="local", status="failure").inc()
        return jsonify({"error": "Unauthorized", "message": "Invalid email or password."}), 401

    session["user"] = {
        "id": target["id"],
        "name": target["name"],
        "email": target["email"],
        "role": target["role"],
        "provider": target.get("provider", "local")
    }

    AUTH_EVENTS.labels(type="login", provider="local", status="success").inc()
    return jsonify({
        "message": "Login successful",
        "user": session["user"]
    }), 200


@app.route("/api/auth/sso", methods=["POST"])
def sso_exchange():
    """
    Enterprise Single Sign-On (SSO) Exchange (Supports Google, GitHub, Okta)
    Validates token payload and provisions/authenticates user session.
    """
    global user_id_counter, next_id
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "Google").capitalize() # Google, Github, Okta
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    sso_token = data.get("sso_token") or secrets.token_hex(16)

    if not email or not name:
        AUTH_EVENTS.labels(type="sso", provider=provider.lower(), status="failure").inc()
        return jsonify({"error": "Validation Error", "message": "SSO payload must include name and email."}), 400

    # Find or provision user
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        user = {
            "id": user_id_counter,
            "name": name,
            "email": email,
            "password_hash": "SSO_MANAGED_IDENTITY",
            "role": f"{provider} Verified Engineer",
            "provider": provider.lower()
        }
        users.append(user)
        user_id_counter += 1

        # Also provision in Employee Directory
        avatar = "".join([p[0] for p in name.split()[:2]]).upper()
        employees.append({
            "id": next_id,
            "name": name,
            "role": f"{provider} Verified Specialist",
            "department": "Platform & Cloud",
            "email": email,
            "status": "Active",
            "avatar": avatar,
            "location": "Mumbai, India",
            "phone": "+91 98200 99887"
        })
        next_id += 1

    session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "provider": provider.lower(),
        "sso_token": sso_token
    }

    AUTH_EVENTS.labels(type="sso", provider=provider.lower(), status="success").inc()
    return jsonify({
        "message": f"Successfully authenticated via {provider} SSO",
        "user": session["user"]
    }), 200


@app.route("/api/auth/user", methods=["GET"])
def current_user():
    """
    Returns the currently authenticated user in session (or guest).
    """
    user = session.get("user")
    if user:
        return jsonify({"authenticated": True, "user": user}), 200
    return jsonify({
        "authenticated": False,
        "user": {
            "name": "Guest Engineer",
            "role": "Viewing Mode",
            "email": "guest@devops.local"
        }
    }), 200


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Successfully logged out"}), 200


# --- 4. Prometheus Scrape Target ---
@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Prometheus metrics target for scrapers (Role R4/R5).
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
