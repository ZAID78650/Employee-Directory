"""
Unit tests for Employee Directory API
Meets Practical 10 requirements: '1 simple test' (and comprehensive endpoint tests)
"""

import pytest
import json
from app import app, employees


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test GET /health returns 200 OK and valid status"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "OK"
    assert "Employee Directory" in data["service"]


def test_get_items(client):
    """Test GET /items returns array of employees"""
    response = client.get("/items")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "role" in data[0]


def test_post_item_success(client):
    """Test POST /items successfully creates a new employee"""
    new_employee = {
        "name": "DevOps Candidate",
        "role": "Cloud Architect",
        "department": "Platform",
        "email": "devops@company.com",
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
    assert res_data["item"]["name"] == "DevOps Candidate"
    assert res_data["item"]["id"] is not None


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


def test_auth_google_login(client):
    """Test POST /api/auth/google logs in and sets session"""
    google_payload = {
        "name": "Google Test Engineer",
        "email": "google.tester@student.college.edu",
        "picture": "https://lh3.googleusercontent.com/test",
        "provider": "google",
        "role": "Cloud Tester",
        "department": "Platform & Cloud"
    }
    response = client.post(
        "/api/auth/google",
        data=json.dumps(google_payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Google authentication successful"
    assert data["user"]["email"] == "google.tester@student.college.edu"


def test_auth_sso_endpoint(client):
    """Test POST /api/auth/sso logs in via SSO provider and auto-provisions user"""
    sso_payload = {
        "provider": "google",
        "name": "Zaid Shaikh",
        "email": "szaid8364@eng.rizvi.edu.in",
        "role": "Lead DevOps Architect",
        "department": "Engineering"
    }
    response = client.post(
        "/api/auth/sso",
        data=json.dumps(sso_payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "successful" in data["message"]
    assert data["user"]["email"] == "szaid8364@eng.rizvi.edu.in"
    with client.session_transaction() as sess:
        assert sess.get("user") is not None
        assert sess["user"]["email"] == "szaid8364@eng.rizvi.edu.in"


def test_auth_signup_and_login(client):
    """Test standard signup and login endpoints"""
    signup_payload = {
        "name": "New Developer",
        "email": "developer@student.college.edu",
        "password": "securepassword123",
        "department": "AI & Data Science"
    }
    signup_res = client.post(
        "/api/auth/signup",
        data=json.dumps(signup_payload),
        content_type="application/json"
    )
    assert signup_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        data=json.dumps({
            "email": "developer@student.college.edu",
            "password": "securepassword123"
        }),
        content_type="application/json"
    )
    assert login_res.status_code == 200
    assert login_res.get_json()["user"]["email"] == "developer@student.college.edu"


def test_google_oauth_redirect_unconfigured(client, monkeypatch):
    """Test GET /auth/google seamlessly authenticates and redirects to dashboard in dev mode"""
    import app as app_module
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_SECRET", "")
    
    response = client.get("/auth/google", follow_redirects=False)
    assert response.status_code == 302
    assert response.location in ["/", "/dashboard"]
    with client.session_transaction() as sess:
        assert sess.get("user") is not None
        assert sess["user"]["email"] == "szaid8364@gmail.com"


def test_google_oauth_redirect_configured(client, monkeypatch):
    """Test GET /auth/google redirects to accounts.google.com with valid state and prompt=select_account when configured"""
    import app as app_module
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    
    response = client.get("/auth/google", follow_redirects=False)
    assert response.status_code == 302
    assert "accounts.google.com" in response.location
    assert "client_id=test-client-id.apps.googleusercontent.com" in response.location
    assert "response_type=code" in response.location
    assert "prompt=select_account" in response.location
    assert "state=" in response.location


def test_google_oauth_callback_access_denied(client):
    """Test GET /auth/google/callback redirects with access_denied error when user cancels"""
    response = client.get("/auth/google/callback?error=access_denied", follow_redirects=False)
    assert response.status_code == 302
    assert "error=access_denied" in response.location


def test_google_oauth_callback_state_mismatch(client):
    """Test GET /auth/google/callback blocks requests with invalid or missing CSRF state"""
    with client.session_transaction() as sess:
        sess["oauth_state"] = "valid_state_123"
    
    response = client.get("/auth/google/callback?code=mock_code&state=wrong_state", follow_redirects=False)
    assert response.status_code == 302
    assert "error=invalid_state" in response.location


def test_google_oauth_callback_success(client, monkeypatch):
    """Test full GET /auth/google/callback exchanges code, fetches profile, and creates session"""
    import app as app_module
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_SECRET", "test-secret")

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code

        def json(self):
            return self._json_data

    def mock_post(url, *args, **kwargs):
        if "oauth2.googleapis.com/token" in url:
            return MockResponse({"access_token": "mock-access-token-xyz"})
        return MockResponse({}, 404)

    def mock_get(url, *args, **kwargs):
        if "googleapis.com/oauth2/v3/userinfo" in url:
            return MockResponse({
                "sub": "998877665544",
                "name": "Alex Mercer",
                "email": "alex.mercer@student.college.edu",
                "picture": "https://lh3.googleusercontent.com/avatar",
                "email_verified": True
            })
        return MockResponse({}, 404)

    monkeypatch.setattr(app_module.requests, "post", mock_post)
    monkeypatch.setattr(app_module.requests, "get", mock_get)

    # Set session state
    with client.session_transaction() as sess:
        sess["oauth_state"] = "secure_state_token_456"

    response = client.get("/auth/google/callback?code=valid_code_abc&state=secure_state_token_456", follow_redirects=False)
    assert response.status_code == 302
    assert response.location in ["/", "/dashboard"]

    # Verify session user is authenticated
    with client.session_transaction() as sess:
        assert sess.get("user") is not None
        assert sess["user"]["email"] == "alex.mercer@student.college.edu"
        assert sess["user"]["name"] == "Alex Mercer"
        assert sess["user"]["google_sub"] == "998877665544"


def test_dashboard_access_and_logout(client):
    """Test unauthorized access redirects to login and logout clears session"""
    # Unauthorized access to / and /dashboard
    res1 = client.get("/", follow_redirects=False)
    assert res1.status_code == 302
    assert "login" in res1.location

    res2 = client.get("/dashboard", follow_redirects=False)
    assert res2.status_code == 302
    assert "login" in res2.location

    # Authenticate and test logout
    with client.session_transaction() as sess:
        sess["user"] = {"name": "Test User", "email": "test@company.com"}

    dash_res = client.get("/dashboard", follow_redirects=False)
    assert dash_res.status_code == 200

    logout_res = client.get("/logout", follow_redirects=False)
    assert logout_res.status_code == 302
    with client.session_transaction() as sess:
        assert "user" not in sess


def test_attendance_endpoints(client):
    """Test attendance API endpoints: get, checkin toggle, mode switch, leave schedule, and export"""
    # 1. GET /api/attendance
    res = client.get("/api/attendance")
    assert res.status_code == 200
    data = res.get_json()
    assert "roster" in data
    assert "summary" in data
    assert len(data["roster"]) >= 4
    assert data["summary"]["presentToday"] >= 1

    # 2. POST /api/attendance/checkin
    checkin_res = client.post(
        "/api/attendance/checkin",
        data=json.dumps({"employee_id": 1}),
        content_type="application/json"
    )
    assert checkin_res.status_code == 200
    checkin_data = checkin_res.get_json()
    assert "record" in checkin_data
    assert checkin_data["record"]["emp_id"] == 1

    # Toggle back to original state
    client.post(
        "/api/attendance/checkin",
        data=json.dumps({"employee_id": 1}),
        content_type="application/json"
    )

    # 3. POST /api/attendance/mode
    mode_res = client.post(
        "/api/attendance/mode",
        data=json.dumps({"employee_id": 2, "mode": "On-Premises (Lab)"}),
        content_type="application/json"
    )
    assert mode_res.status_code == 200
    assert mode_res.get_json()["record"]["mode"] == "On-Premises (Lab)"

    # 4. POST /api/attendance/leave
    leave_res = client.post(
        "/api/attendance/leave",
        data=json.dumps({
            "employee_id": 3,
            "leave_type": "Sick Leave",
            "days": 1,
            "start_date": "2026-10-05",
            "reason": "Health Check"
        }),
        content_type="application/json"
    )
    assert leave_res.status_code == 200
    assert leave_res.get_json()["record"]["status"] == "On Leave"

    # 5. GET /api/attendance/export
    export_res = client.get("/api/attendance/export")
    assert export_res.status_code == 200
    assert export_res.mimetype == "text/csv"
    assert b"Personnel Name" in export_res.data


def test_export_directory_csv(client):
    """Test GET /api/export/csv exports directory records in CSV format"""
    res = client.get("/api/export/csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert b"Name,Role,Department,Email" in res.data


def test_system_health_and_activity(client):
    """Test /api/system/health and /api/activity endpoints"""
    health_res = client.get("/api/system/health")
    assert health_res.status_code == 200
    health_data = health_res.get_json()
    assert "services" in health_data
    assert "apiServer" in health_data["services"]
    assert "database" in health_data["services"]

    act_res = client.get("/api/activity")
    assert act_res.status_code == 200
    act_data = act_res.get_json()
    assert isinstance(act_data, list)


def test_security_scan_and_ai_defense(client):
    """Test /api/security/scan and /api/security/ai-optimize endpoints"""
    # 1. GET & POST /api/security/scan
    scan_res = client.post("/api/security/scan")
    assert scan_res.status_code == 200
    scan_data = scan_res.get_json()
    assert scan_data["status"] == "Success"
    assert scan_data["grade"] == "A+"
    assert scan_data["score"] >= 99.0
    assert "checks" in scan_data
    assert len(scan_data["checks"]) >= 5
    assert "aiDefense" in scan_data

    # 2. POST /api/security/ai-optimize
    opt_res = client.post("/api/security/ai-optimize")
    assert opt_res.status_code == 200
    opt_data = opt_res.get_json()
    assert opt_data["status"] == "Optimized"
    assert len(opt_data["optimizations"]) >= 3

    # 3. POST /api/security/test-token
    token_res = client.post("/api/security/test-token")
    assert token_res.status_code == 200
    token_data = token_res.get_json()
    assert token_data["algorithm"] == "RS256"
    assert token_data["status"] == "VALID_SIGNATURE"

    # 4. GET /api/security/inspect-session
    sess_res = client.get("/api/security/inspect-session")
    assert sess_res.status_code == 200
    sess_data = sess_res.get_json()
    assert "cookieDirectives" in sess_data
    assert sess_data["cookieDirectives"]["httpOnly"] is True

    # 5. POST /api/security/rbac-probe
    rbac_res = client.post("/api/security/rbac-probe")
    assert rbac_res.status_code == 200
    rbac_data = rbac_res.get_json()
    assert rbac_data["unauthorizedProbe"]["result"] == "403 Forbidden"
    assert rbac_data["authorizedProbe"]["result"] == "200 OK"

    # 6. GET /api/security/posture
    posture_res = client.get("/api/security/posture")
    assert posture_res.status_code == 200
    posture_data = posture_res.get_json()
    assert posture_data["securityGrade"] == "A+"
    assert "SOC-2 Type II" in posture_data["compliance"]


def test_login_page_renders_badge_and_google_sso(client):
    """Test GET /login renders 3D metallic shield badge, Google auth button, and account chooser modal"""
    response = client.get("/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "advanced_employee_directory_logo.png" in html
    assert "floating-shield" in html
    assert "googleAccountModal" in html
    assert "openGoogleAccountChooser" in html
    assert "Sign in with Google" in html


def test_google_create_account_sso_flow(client):
    """Test POST /api/auth/sso provisions a new Google account and registers employee"""
    new_email = "new.google.user@eng.rizvi.edu.in"
    payload = {
        "provider": "google",
        "name": "New Google Candidate",
        "email": new_email,
        "role": "Full Stack Engineer",
        "department": "Engineering"
    }
    response = client.post(
        "/api/auth/sso",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["email"] == new_email
    assert data["redirect"] == "/"

    # Verify session is populated
    with client.session_transaction() as sess:
        assert sess.get("user") is not None
        assert sess["user"]["email"] == new_email

    # Verify employee record is auto-provisioned
    emp_res = client.get("/items")
    assert emp_res.status_code == 200
    items = emp_res.get_json()
    assert any(e["email"].lower() == new_email.lower() for e in items)


def test_developer_sso_github_gitlab(client):
    """Test POST /api/auth/sso for GitHub and GitLab providers"""
    for prov in ["github", "gitlab"]:
        payload = {
            "provider": prov,
            "name": f"Developer {prov.title()}",
            "email": f"dev.{prov}@student.college.edu"
        }
        res = client.post("/api/auth/sso", data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert data["user"]["auth_provider"] == prov
