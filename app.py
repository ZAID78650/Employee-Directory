"""
Employee Directory REST API & Web Application
Practical 10: End-to-End DevOps Pipeline (B3-G3: Employee Directory)
"""

import time
import os
from flask import Flask, request, jsonify, render_template, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

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

# In-memory storage for Employee Directory as required by rubric
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
        "uptime": "healthy"
    }), 200


@app.route("/items", methods=["GET"])
def get_items():
    """
    Mandatory Endpoint 2:
    GET /items : returns the list of items for the topic (Employee Directory).
    Supports query parameter filtering by department or search term.
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


# --- Additional REST APIs for Professional Experience (Delete & Single item) ---
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


# --- 3. Prometheus Scrape Target ---
@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Prometheus metrics target for scrapers (Role R4/R5).
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
