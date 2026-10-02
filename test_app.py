"""
Comprehensive Unit & Integration Test Suite for Employee Directory
Includes:
- Practical 10 Endpoints (/health, /items GET, /items POST)
- Authentication (/api/auth/register, /api/auth/login, /api/auth/logout)
- SSO Integration (/api/auth/sso for Google, GitHub, Okta)
- Prometheus Scrape Target (/metrics)
"""

import pytest
import json
from app import app, employees, users


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- 1. Practical 10 Mandatory Endpoints Tests ---

def test_health_check(client):
    """Test GET /health returns 200 OK and valid status"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "OK"
    assert "Employee Directory" in data["service"]
    assert data.get("sso_ready") is True


def test_get_items(client):
    """Test GET /items returns array of employees including batch B3-G3 members"""
    response = client.get("/items")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 4
    names = [e["name"] for e in data]
    assert "SHAIKH ZAID MATINUDDIN" in names
    assert "SHAIKH RAHMAT" in names


def test_post_item_success(client):
    """Test POST /items successfully creates a new employee"""
    new_employee = {
        "name": "Prof. DevOps Evaluator",
        "role": "Lab Examiner",
        "department": "Platform & Cloud",
        "email": "examiner@college.edu",
        "status": "Active"
    }
    response = client.post(
        "/items",
        data=json.dumps(new_employee),
        content_type="application/json"
    )
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["message"] == "Employee added successfully"
    assert res_data["item"]["name"] == "Prof. DevOps Evaluator"


def test_post_item_validation_failure(client):
    """Test POST /items returns 400 when missing required fields"""
    bad_employee = {"email": "no_name@company.com"}
    response = client.post(
        "/items",
        data=json.dumps(bad_employee),
        content_type="application/json"
    )
    assert response.status_code == 400
    res_data = response.get_json()
    assert "error" in res_data


def test_metrics_endpoint(client):
    """Test GET /metrics returns prometheus scrape format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.data


# --- 2. Authentication & Sign Up Tests ---

def test_register_and_create_account(client):
    """Test POST /api/auth/register creates a new user and session"""
    payload = {
        "name": "Dr. Alan Turing",
        "email": "alan.turing@research.org",
        "password": "SecurePassword123!",
        "role": "Principal Researcher",
        "department": "AI & Data Science"
    }
    response = client.post(
        "/api/auth/register",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Account created successfully"
    assert data["user"]["email"] == "alan.turing@research.org"


def test_register_duplicate_email(client):
    """Test POST /api/auth/register returns 409 Conflict for existing email"""
    payload = {
        "name": "Duplicate User",
        "email": "zaid.matinuddin@student.college.edu",
        "password": "Password123!"
    }
    response = client.post(
        "/api/auth/register",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 409


def test_login_success_and_failure(client):
    """Test POST /api/auth/login credentials verification"""
    # Success
    good_creds = {
        "email": "zaid.matinuddin@student.college.edu",
        "password": "DevOps@2026"
    }
    res_good = client.post("/api/auth/login", data=json.dumps(good_creds), content_type="application/json")
    assert res_good.status_code == 200
    assert res_good.get_json()["user"]["name"] == "SHAIKH ZAID MATINUDDIN"

    # Failure
    bad_creds = {
        "email": "zaid.matinuddin@student.college.edu",
        "password": "WrongPassword!"
    }
    res_bad = client.post("/api/auth/login", data=json.dumps(bad_creds), content_type="application/json")
    assert res_bad.status_code == 401


# --- 3. Single Sign-On (SSO) Integration Tests ---

def test_sso_google_integration(client):
    """Test POST /api/auth/sso with Google provider payload"""
    sso_payload = {
        "provider": "google",
        "name": "Google SSO User",
        "email": "google.devops@gmail.com",
        "sso_token": "mock-google-oauth2-token-xyz"
    }
    response = client.post(
        "/api/auth/sso",
        data=json.dumps(sso_payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "Google SSO" in data["message"]
    assert data["user"]["provider"] == "google"
    assert data["user"]["email"] == "google.devops@gmail.com"


def test_sso_github_integration(client):
    """Test POST /api/auth/sso with GitHub provider payload"""
    sso_payload = {
        "provider": "github",
        "name": "GitHub Octocat",
        "email": "octocat@github.com",
        "sso_token": "ghp_mocktoken987654321"
    }
    response = client.post(
        "/api/auth/sso",
        data=json.dumps(sso_payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "Github SSO" in data["message"] or "GitHub SSO" in data["message"]
    assert data["user"]["provider"] == "github"


def test_auth_current_user_and_logout(client):
    """Test GET /api/auth/user and POST /api/auth/logout session lifecycle"""
    # 1. Login
    client.post(
        "/api/auth/login",
        data=json.dumps({"email": "shaikh.rahmat@student.college.edu", "password": "DevOps@2026"}),
        content_type="application/json"
    )
    # 2. Check current session
    res_user = client.get("/api/auth/user")
    assert res_user.status_code == 200
    assert res_user.get_json()["authenticated"] is True
    assert res_user.get_json()["user"]["name"] == "SHAIKH RAHMAT"

    # 3. Logout
    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200

    # 4. Check guest state
    res_guest = client.get("/api/auth/user")
    assert res_guest.get_json()["authenticated"] is False
