"""
End-to-End DevOps Pipeline & Enterprise Employee Directory
Practical 10: Agile Software Development & DevOps Lab (2015119)
Course: TE AI&DS | Batch B3 - Group B3-G3

Role Responsibilities:
- R1: Agile Planner & Documentation Lead (Roll 67)
- R2: Developer & Version Control Engineer (Roll 56)
- R3: CI/CD & Containerization Engineer (Roll 60 - Shaikh Zaid Matinuddin)
- R4: Deployment & Monitoring Engineer (Roll 61)
"""

import os
import time
from flask import Flask, request, jsonify, render_template, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Initialize Flask WSGI Application
app = Flask(__name__, template_folder="templates", static_folder="static")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Prometheus Telemetry Instrumentation
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["endpoint", "method", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP Request Duration in Seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

# Start timestamp for uptime calculation
START_TIME = time.time()

# Seed Enterprise Roster Database (In-Memory Data Store)
INITIAL_EMPLOYEES = [
    {
        "id": 1,
        "name": "SHAIKH RAHMAT",
        "role": "Agile Planner & Documentation Lead (R1)",
        "department": "Platform & Cloud",
        "email": "shaikh.rahmat@student.college.edu",
        "phone": "+91 98201 11234",
        "location": "Mumbai, India",
        "avatar": "SR",
        "status": "Active"
    },
    {
        "id": 2,
        "name": "YADGIR ZUVERIA SALIM",
        "role": "Developer & Version Control (R2)",
        "department": "AI & Data Science",
        "email": "zuveria.yadgir@student.college.edu",
        "phone": "+91 98202 22345",
        "location": "Mumbai, India",
        "avatar": "YZ",
        "status": "Active"
    },
    {
        "id": 3,
        "name": "SHAIKH ZAID MATINUDDIN",
        "role": "CI/CD & Containerization Engineer (R3)",
        "department": "Core Infrastructure",
        "email": "zaid.matinuddin@student.college.edu",
        "phone": "+91 98203 33456",
        "location": "Mumbai, India",
        "avatar": "ZM",
        "status": "Active"
    },
    {
        "id": 4,
        "name": "SHAIKH ZAID WAZIDALI",
        "role": "Deployment & Monitoring Engineer (R4)",
        "department": "Core Infrastructure",
        "email": "zaid.wazidali@student.college.edu",
        "phone": "+91 98204 44567",
        "location": "Mumbai, India",
        "avatar": "ZW",
        "status": "Active"
    }
]

# Mutable list for runtime persistence
employees = [dict(emp) for emp in INITIAL_EMPLOYEES]

def reset_employees():
    """Helper for testing: reset employee store to initial state."""
    global employees
    employees = [dict(emp) for emp in INITIAL_EMPLOYEES]


@app.before_request
def record_request_start():
    request._start_time = time.time()


@app.after_request
def record_metrics_after(response):
    if request.path != "/metrics":
        latency = time.time() - getattr(request, "_start_time", time.time())
        endpoint = request.path
        method = request.method
        status = str(response.status_code)
        
        HTTP_REQUESTS_TOTAL.labels(endpoint=endpoint, method=method, status=status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(endpoint=endpoint).observe(latency)
    return response


# ==============================================================================
# REST Endpoints (Engineered by Role R2, Verified by Role R3 CI)
# ==============================================================================

@app.route("/health", methods=["GET"])
def health():
    """Operational Heartbeat Endpoint for Docker and Prometheus Health Checks."""
    return jsonify({
        "status": "OK",
        "service": "Employee Directory Service",
        "uptime": "healthy",
        "version": "1.0.0"
    }), 200


@app.route("/items", methods=["GET"])
def get_items():
    """Retrieve employee listings with query parameter filtering."""
    dept = request.args.get("department")
    search_q = request.args.get("search")
    
    filtered = employees
    
    if dept and dept != "All":
        filtered = [e for e in filtered if e.get("department", "").lower() == dept.lower()]
        
    if search_q:
        q = search_q.lower()
        filtered = [
            e for e in filtered
            if q in e.get("name", "").lower() or q in e.get("email", "").lower()
        ]
        
    return jsonify(filtered), 200


@app.route("/items", methods=["POST"])
def add_item():
    """Register a new employee record with validation and schema enforcement."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
        
    name = (data.get("name") or "").strip()
    role = (data.get("role") or "").strip()
    department = (data.get("department") or "Engineering").strip()
    email = (data.get("email") or "").strip().lower()
    
    if not name or not role:
        return jsonify({"error": "Fields 'name' and 'role' are required"}), 400
        
    # Generate initials avatar
    name_parts = name.split()
    avatar = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "EM"
    
    new_employee = {
        "id": int(time.time() * 1000),
        "name": name,
        "role": role,
        "department": department,
        "email": email or f"{name.lower().replace(' ', '.')}@enterprise.internal",
        "phone": (data.get("phone") or "+91 98000 00000").strip(),
        "location": (data.get("location") or "Mumbai, India").strip(),
        "avatar": avatar,
        "status": "Active"
    }
    employees.append(new_employee)
    return jsonify(new_employee), 201


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus Scrape Endpoint exposing runtime telemetry in OpenMetrics standard format."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# ==============================================================================
# UI & Dashboard Endpoints
# ==============================================================================

@app.route("/", methods=["GET"])
def index():
    """Render executive web dashboard or redirect to UI view."""
    return render_template("index.html", employees=employees)


@app.route("/login", methods=["GET"])
def login():
    """Enterprise authentication and SSO login portal view."""
    return render_template("login.html")


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Live telemetry KPI statistics for web dashboard widgets."""
    uptime_seconds = int(time.time() - START_TIME)
    total_depts = len(set(e.get("department") for e in employees))
    return jsonify({
        "total_employees": len(employees),
        "active_departments": total_depts,
        "uptime_seconds": uptime_seconds,
        "service_health": "Healthy (100% Uptime)",
        "version": "1.0.0"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"[*] Starting Employee Directory Microservice on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
