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

# In-memory storage for Employee Directory (Preserves B3-G3 & expands enterprise directory)
employees = [
    {
        "id": 1,
        "name": "Zaid Shaikh",
        "role": "Admin",
        "department": "DevOps",
        "email": "zaid@company.com",
        "status": "Online",
        "avatar": "ZS",
        "location": "Mumbai",
        "phone": "+91 98200 99887",
        "deployments": 28,
        "commits": 142,
        "prs": 19,
        "sso": "Google SSO Connected",
        "last_login": "Today at 06:38 PM",
        "permissions": "Full Admin Access"
    },
    {
        "id": 2,
        "name": "Aarav Patil",
        "role": "Developer",
        "department": "Backend",
        "email": "aarav@company.com",
        "status": "Online",
        "avatar": "AP",
        "location": "Pune",
        "phone": "+91 98201 22334",
        "deployments": 14,
        "commits": 88,
        "prs": 12,
        "sso": "Google SSO Connected",
        "last_login": "Today at 05:12 PM",
        "permissions": "Developer Read/Write"
    },
    {
        "id": 3,
        "name": "Sneha More",
        "role": "Developer",
        "department": "Frontend",
        "email": "sneha@company.com",
        "status": "Online",
        "avatar": "SM",
        "location": "Mumbai",
        "phone": "+91 98202 33445",
        "deployments": 9,
        "commits": 64,
        "prs": 15,
        "sso": "GitHub SSO",
        "last_login": "Today at 04:45 PM",
        "permissions": "Developer Read/Write"
    },
    {
        "id": 4,
        "name": "Rohan Deshmukh",
        "role": "DevOps",
        "department": "Infrastructure",
        "email": "rohan@company.com",
        "status": "Online",
        "avatar": "RD",
        "location": "Bengaluru",
        "phone": "+91 98203 44556",
        "deployments": 36,
        "commits": 112,
        "prs": 22,
        "sso": "Google SSO Connected",
        "last_login": "Today at 06:15 PM",
        "permissions": "Infra & K8s Admin"
    },
    {
        "id": 5,
        "name": "Priya Sharma",
        "role": "QA",
        "department": "Quality Assurance",
        "email": "priya@company.com",
        "status": "Offline",
        "avatar": "PS",
        "location": "Delhi",
        "phone": "+91 98204 55667",
        "deployments": 5,
        "commits": 31,
        "prs": 8,
        "sso": "Google SSO Connected",
        "last_login": "Yesterday at 07:30 PM",
        "permissions": "QA Tester"
    },
    {
        "id": 6,
        "name": "SHAIKH RAHMAT",
        "role": "Agile Planner & Documentation Lead (R1)",
        "department": "Platform & Cloud",
        "email": "shaikh.rahmat@student.college.edu",
        "status": "Online",
        "avatar": "SR",
        "location": "Mumbai",
        "phone": "+91 98201 11234",
        "deployments": 12,
        "commits": 45,
        "prs": 9,
        "sso": "Google SSO Connected",
        "last_login": "Today at 06:00 PM",
        "permissions": "Jira & Agile Planner"
    },
    {
        "id": 7,
        "name": "YADGIR ZUVERIA SALIM",
        "role": "Developer & Version Control (R2)",
        "department": "AI & Data Science",
        "email": "zuveria.yadgir@student.college.edu",
        "status": "Online",
        "avatar": "YZ",
        "location": "Pune",
        "phone": "+91 98202 22345",
        "deployments": 18,
        "commits": 95,
        "prs": 14,
        "sso": "GitHub SSO",
        "last_login": "Today at 05:40 PM",
        "permissions": "Developer Read/Write"
    },
    {
        "id": 8,
        "name": "SHAIKH ZAID MATINUDDIN",
        "role": "CI/CD & Containerization Engineer (R3)",
        "department": "DevOps",
        "email": "zaid.matinuddin@student.college.edu",
        "status": "Online",
        "avatar": "ZM",
        "location": "Mumbai",
        "phone": "+91 98203 33456",
        "deployments": 42,
        "commits": 160,
        "prs": 27,
        "sso": "Google SSO Connected",
        "last_login": "Just now",
        "permissions": "CI/CD Full Access"
    },
    {
        "id": 9,
        "name": "SHAIKH ZAID WAZIDALI",
        "role": "Deployment & Monitoring Engineer (R4)",
        "department": "Infrastructure",
        "email": "zaid.wazidali@student.college.edu",
        "status": "Online",
        "avatar": "ZW",
        "location": "Bengaluru",
        "phone": "+91 98204 44567",
        "deployments": 31,
        "commits": 104,
        "prs": 18,
        "sso": "Prometheus/Grafana Lead",
        "last_login": "Today at 06:20 PM",
        "permissions": "Monitoring & Telemetry Admin"
    }
]
next_id = 10


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


# --- 1. Web UI Routes ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/auth", methods=["GET"])
def auth_page():
    """
    Dedicated Login, Sign Up, and SSO Authentication Page
    """
    return render_template("auth.html")


@app.route("/auth/google/callback", methods=["GET"])
def google_callback():
    """
    Receives Google OAuth Redirect with query parameters: email, name, action
    Provisions session and redirects straight to /
    """
    global user_id_counter, next_id
    email = request.args.get("email", "zaid.shaikh@gmail.com").strip().lower()
    name = request.args.get("name", "SHAIKH ZAID").strip()
    action = request.args.get("action", "signin")

    user = next((u for u in users if u["email"] == email), None)
    if not user:
        user = {
            "id": user_id_counter,
            "name": name,
            "email": email,
            "password_hash": "GOOGLE_ACCOUNTS_VERIFIED",
            "role": "Google Verified Engineer",
            "provider": "google"
        }
        users.append(user)
        user_id_counter += 1

        if not any(e["email"].lower() == email for e in employees):
            avatar = "".join([p[0] for p in name.split()[:2]]).upper() if name else "G"
            employees.append({
                "id": next_id,
                "name": name,
                "role": "Google Verified Specialist",
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
        "provider": "google",
        "action": action
    }

    AUTH_EVENTS.labels(type="sso", provider="google", status="success").inc()
    return render_template("auth_callback.html", user=session["user"])


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


@app.route("/items/<int:emp_id>", methods=["PUT", "PATCH"])
def update_item(emp_id):
    global employees
    employee = next((e for e in employees if e["id"] == emp_id), None)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({"error": "Validation Failed", "message": "No data provided"}), 400

    if "name" in data and data["name"].strip():
        employee["name"] = data["name"].strip()
        parts = employee["name"].split()
        employee["avatar"] = "".join([p[0] for p in parts[:2]]).upper()
    if "role" in data and data["role"].strip():
        employee["role"] = data["role"].strip()
    if "department" in data:
        employee["department"] = data["department"].strip()
    if "email" in data:
        employee["email"] = data["email"].strip().lower()
    if "status" in data:
        employee["status"] = data["status"].strip()
    if "location" in data:
        employee["location"] = data["location"].strip()
    if "phone" in data:
        employee["phone"] = data["phone"].strip()

    return jsonify({"message": "Employee updated successfully", "item": employee}), 200


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
    Enterprise Single Sign-On (SSO) Exchange (Supports Google Accounts, GitHub, Okta).
    Parses real Google Identity Services JWT id_tokens or mock OAuth payloads.
    """
    global user_id_counter, next_id
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "Google").capitalize()
    
    # Handle Google One Tap / Sign in with Google (credential is JWT)
    credential = data.get("credential")
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    picture = data.get("picture")

    if credential and not email:
        try:
            # Parse unverified JWT payload header.payload.signature
            import base64
            parts = credential.split(".")
            if len(parts) >= 2:
                # Add padding if required
                payload_part = parts[1]
                padded = payload_part + '=' * (-len(payload_part) % 4)
                decoded = base64.urlsafe_b64decode(padded).decode('utf-8')
                jwt_data = json.loads(decoded)
                email = (jwt_data.get("email") or "").strip().lower()
                name = (jwt_data.get("name") or "").strip()
                picture = jwt_data.get("picture")
        except Exception as e:
            app.logger.warning(f"Error parsing Google JWT: {e}")

    sso_token = credential or data.get("sso_token") or secrets.token_hex(16)

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
            "password_hash": "GOOGLE_SSO_IDENTITY",
            "role": f"{provider} Verified Engineer",
            "provider": provider.lower(),
            "picture": picture
        }
        users.append(user)
        user_id_counter += 1

        # Also provision in Employee Directory
        avatar = "".join([p[0] for p in name.split()[:2]]).upper() if name else "G"
        employees.append({
            "id": next_id,
            "name": name,
            "role": f"{provider} Verified Specialist",
            "department": "Platform & Cloud",
            "email": email,
            "status": "Active",
            "avatar": avatar,
            "picture": picture,
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
        "picture": picture or user.get("picture"),
        "sso_token": sso_token[:16] + "..." if len(sso_token) > 16 else sso_token
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
