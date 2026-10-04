"""
Unit and Integration Tests for Employee Directory API & Authentication Suite
Practical 10: End-to-End DevOps Pipeline (B3-G3: Employee Directory)
Verifies:
- Standard Email/Password authentication & Werkzeug password hashing
- Account creation with validation, length checks, and duplicate detection
- Real Google, GitHub, and GitLab OAuth flows (redirection, CSRF state, token exchange, profile provisioning)
- Session persistence, HttpOnly cookie security, and protected dashboard routing
"""

import pytest
import json
from werkzeug.security import check_password_hash
from app import app, employees, registered_users


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- 1. Basic Health and Directory API Tests ---

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


# --- 2. Real Email / Password Authentication & Hashing Tests ---

def test_auth_signup_validation_and_duplicate(client):
    """Test POST /api/auth/signup validation, duplicate detection, and secure password hashing"""
    # 1. Missing fields
    res_missing = client.post("/api/auth/signup", data=json.dumps({}), content_type="application/json")
    assert res_missing.status_code == 400

    # 2. Short password (< 6 chars)
    res_short = client.post("/api/auth/signup", data=json.dumps({
        "name": "Short Pwd",
        "email": "short.pwd@student.college.edu",
        "password": "123"
    }), content_type="application/json")
    assert res_short.status_code == 400

    # 3. Mismatched confirmation password
    res_mismatch = client.post("/api/auth/signup", data=json.dumps({
        "name": "Mismatch Tester",
        "email": "mismatch@student.college.edu",
        "password": "securepassword123",
        "confirmPassword": "differentpassword"
    }), content_type="application/json")
    assert res_mismatch.status_code == 400

    # 4. Successful registration
    signup_payload = {
        "name": "Valid Engineer",
        "email": "valid.engineer@student.college.edu",
        "password": "securepassword123",
        "confirmPassword": "securepassword123",
        "department": "Engineering"
    }
    res_success = client.post("/api/auth/signup", data=json.dumps(signup_payload), content_type="application/json")
    assert res_success.status_code == 201
    data = res_success.get_json()
    assert data["message"] == "Account created successfully"
    assert data["user"]["email"] == "valid.engineer@student.college.edu"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Verify password was hashed with Werkzeug (never plaintext)
    stored_user = registered_users["valid.engineer@student.college.edu"]
    assert "password" not in stored_user
    assert stored_user.get("password_hash") is not None
    assert stored_user["password_hash"] != "securepassword123"
    assert check_password_hash(stored_user["password_hash"], "securepassword123") is True

    # 5. Duplicate account detection -> 409 Conflict
    res_dup = client.post("/api/auth/signup", data=json.dumps(signup_payload), content_type="application/json")
    assert res_dup.status_code == 409
    dup_data = res_dup.get_json()
    assert dup_data["error"] == "Duplicate Account"


def test_auth_login_validation_and_hash_verification(client):
    """Test POST /api/auth/login credentials verification, hash check, and 401/404 handling"""
    # 1. Missing credentials
    res_missing = client.post("/api/auth/login", data=json.dumps({}), content_type="application/json")
    assert res_missing.status_code == 400

    # 2. Invalid email format
    res_bad_email = client.post("/api/auth/login", data=json.dumps({
        "email": "not-an-email",
        "password": "anypassword"
    }), content_type="application/json")
    assert res_bad_email.status_code == 400

    # 3. Account not found -> 404
    res_404 = client.post("/api/auth/login", data=json.dumps({
        "email": "nonexistent.user@nowhere.com",
        "password": "password123"
    }), content_type="application/json")
    assert res_404.status_code == 404

    # 4. Incorrect password -> 401 Unauthorized
    res_401 = client.post("/api/auth/login", data=json.dumps({
        "email": "zaid.matinuddin@student.college.edu",
        "password": "wrongpassword999"
    }), content_type="application/json")
    assert res_401.status_code == 401
    assert res_401.get_json()["error"] == "Invalid Credentials"

    # 5. Valid credentials -> 200 OK + session established
    res_200 = client.post("/api/auth/login", data=json.dumps({
        "email": "zaid.matinuddin@student.college.edu",
        "password": "password123"
    }), content_type="application/json")
    assert res_200.status_code == 200
    data = res_200.get_json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "zaid.matinuddin@student.college.edu"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]
    assert data["redirect"] in ["/", "/dashboard"]

    # Verify session transaction holds user
    with client.session_transaction() as sess:
        assert sess.get("user") is not None
        assert sess["user"]["email"] == "zaid.matinuddin@student.college.edu"


def test_auth_me_endpoint(client):
    """Test GET /api/auth/me returns 401 when unauthenticated and 200 when logged in"""
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 401

    with client.session_transaction() as sess:
        sess["user"] = {"name": "Session Tester", "email": "session.tester@company.com"}

    res_auth = client.get("/api/auth/me")
    assert res_auth.status_code == 200
    assert res_auth.get_json()["authenticated"] is True


# --- 3. Google OAuth 2.0 Web Client Tests ---

def test_google_oauth_redirect_unconfigured(client, monkeypatch):
    """Test GET /auth/google redirects to /login with informative oauth_not_configured error if credentials missing"""
    import app as app_module
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(app_module, "GOOGLE_CLIENT_SECRET", "")

    response = client.get("/auth/google", follow_redirects=False)
    assert response.status_code == 302
    assert "error=oauth_not_configured" in response.location
    assert "provider=google" in response.location


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


# --- 4. GitHub and GitLab OAuth Tests ---

def test_github_oauth_redirect_and_callback(client, monkeypatch):
    """Test GET /auth/github redirect and callback token exchange"""
    import app as app_module
    
    # 1. Unconfigured
    monkeypatch.setattr(app_module, "GITHUB_CLIENT_ID", "")
    monkeypatch.setattr(app_module, "GITHUB_CLIENT_SECRET", "")
    res_unconf = client.get("/auth/github", follow_redirects=False)
    assert res_unconf.status_code == 302
    assert "error=oauth_not_configured" in res_unconf.location
    assert "provider=github" in res_unconf.location

    # 2. Configured redirect
    monkeypatch.setattr(app_module, "GITHUB_CLIENT_ID", "gh-client-id-123")
    monkeypatch.setattr(app_module, "GITHUB_CLIENT_SECRET", "gh-secret-456")
    res_conf = client.get("/auth/github", follow_redirects=False)
    assert res_conf.status_code == 302
    assert "github.com/login/oauth/authorize" in res_conf.location

    # 3. Successful callback
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code

        def json(self):
            return self._json_data

    def mock_post(url, *args, **kwargs):
        return MockResponse({"access_token": "gh-access-token-789"})

    def mock_get(url, *args, **kwargs):
        if "api.github.com/user/emails" in url:
            return MockResponse([{"email": "github.engineer@student.college.edu", "primary": True, "verified": True}])
        if "api.github.com/user" in url:
            return MockResponse({
                "id": 554433,
                "login": "ghengineer",
                "name": "GitHub Engineer",
                "email": "github.engineer@student.college.edu",
                "avatar_url": "https://avatars.githubusercontent.com/u/554433"
            })
        return MockResponse({}, 404)

    monkeypatch.setattr(app_module.requests, "post", mock_post)
    monkeypatch.setattr(app_module.requests, "get", mock_get)

    with client.session_transaction() as sess:
        sess["github_oauth_state"] = "gh_csrf_state_token"

    res_cb = client.get("/auth/github/callback?code=gh_valid_code&state=gh_csrf_state_token", follow_redirects=False)
    assert res_cb.status_code == 302
    assert res_cb.location in ["/", "/dashboard"]

    with client.session_transaction() as sess:
        assert sess.get("user") is not None
        assert sess["user"]["email"] == "github.engineer@student.college.edu"


def test_gitlab_oauth_redirect_and_callback(client, monkeypatch):
    """Test GET /auth/gitlab redirect and callback flow"""
    import app as app_module

    # 1. Unconfigured
    monkeypatch.setattr(app_module, "GITLAB_CLIENT_ID", "")
    monkeypatch.setattr(app_module, "GITLAB_CLIENT_SECRET", "")
    res_unconf = client.get("/auth/gitlab", follow_redirects=False)
    assert res_unconf.status_code == 302
    assert "error=oauth_not_configured" in res_unconf.location

    # 2. Configured redirect
    monkeypatch.setattr(app_module, "GITLAB_CLIENT_ID", "gl-client-123")
    monkeypatch.setattr(app_module, "GITLAB_CLIENT_SECRET", "gl-secret-456")
    res_conf = client.get("/auth/gitlab", follow_redirects=False)
    assert res_conf.status_code == 302
    assert "gitlab.com/oauth/authorize" in res_conf.location


# --- 5. Protected Dashboard Routing & Session Security Tests ---

def test_dashboard_access_and_logout(client):
    """Test unauthorized access redirects to login and logout clears session"""
    # 1. Unauthorized access to / and /dashboard -> redirect to /login
    res1 = client.get("/", follow_redirects=False)
    assert res1.status_code == 302
    assert "login" in res1.location

    res2 = client.get("/dashboard", follow_redirects=False)
    assert res2.status_code == 302
    assert "login" in res2.location

    # 2. Authenticate session
    with client.session_transaction() as sess:
        sess["user"] = {"name": "Test User", "email": "test@company.com"}

    # Authenticated access to dashboard succeeds
    dash_res = client.get("/dashboard", follow_redirects=False)
    assert dash_res.status_code == 200

    # Authenticated access to /login or /register redirects to /dashboard
    login_redir = client.get("/login", follow_redirects=False)
    assert login_redir.status_code == 302
    assert login_redir.location in ["/", "/dashboard"]

    reg_redir = client.get("/register", follow_redirects=False)
    assert reg_redir.status_code == 302

    # Logout clears session and redirects to /login
    logout_res = client.get("/logout", follow_redirects=False)
    assert logout_res.status_code == 302
    assert "login" in logout_res.location
    with client.session_transaction() as sess:
        assert "user" not in sess


# --- 6. API Endpoints & SSO Utilities ---

def test_auth_google_login(client):
    """Test POST /api/auth/google logs in and sets sanitized session"""
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


def test_attendance_endpoints(client):
    """Test attendance API endpoints: get, checkin toggle, mode switch, leave schedule, and export"""
    res = client.get("/api/attendance")
    assert res.status_code == 200
    data = res.get_json()
    assert "roster" in data
    assert "summary" in data

    checkin_res = client.post(
        "/api/attendance/checkin",
        data=json.dumps({"employee_id": 1}),
        content_type="application/json"
    )
    assert checkin_res.status_code == 200

    # Toggle back
    client.post(
        "/api/attendance/checkin",
        data=json.dumps({"employee_id": 1}),
        content_type="application/json"
    )

    mode_res = client.post(
        "/api/attendance/mode",
        data=json.dumps({"employee_id": 2, "mode": "On-Premises (Lab)"}),
        content_type="application/json"
    )
    assert mode_res.status_code == 200

    export_res = client.get("/api/attendance/export")
    assert export_res.status_code == 200
    assert export_res.mimetype == "text/csv"


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
    assert "services" in health_res.get_json()

    act_res = client.get("/api/activity")
    assert act_res.status_code == 200
    assert isinstance(act_res.get_json(), list)


def test_security_scan_and_ai_defense(client):
    """Test /api/security/scan and posture endpoints"""
    scan_res = client.post("/api/security/scan")
    assert scan_res.status_code == 200
    assert scan_res.get_json()["status"] == "Success"

    sess_res = client.get("/api/security/inspect-session")
    assert sess_res.status_code == 200
    assert sess_res.get_json()["cookieDirectives"]["httpOnly"] is True


def test_login_page_renders_badge_and_google_sso(client):
    """Test GET /login renders 3D metallic shield badge and Google SSO buttons"""
    response = client.get("/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "advanced_employee_directory_logo.png" in html
    assert "floating-shield" in html
    assert "googleAccountModal" in html
    assert "openGoogleAccountChooser" in html
    assert "Sign in with Google" in html
    assert "Create Account with Google" in html


def test_google_create_account_sso_flow(client):
    """Test POST /api/auth/sso provisions a new Google account with action='create' and registers employee"""
    new_email = "new.google.user@eng.rizvi.edu.in"
    payload = {
        "provider": "google",
        "action": "create",
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
    assert data["action"] == "create"
    assert "created and authenticated" in data["message"]
    assert data["user"]["email"] == new_email
    assert data["redirect"] in ["/", "/dashboard"]


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
