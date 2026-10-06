"""
Pytest Automated Test Suite for Enterprise Employee Directory
Practical 10: Agile Software Development & DevOps Lab
Target: 35 passing unit & integration tests as specified in CI/CD pipeline
"""

import pytest
import json
import time
from app import app, reset_employees, INITIAL_EMPLOYEES


@pytest.fixture(autouse=True)
def clean_state():
    """Reset the in-memory employee store before every test run."""
    reset_employees()
    yield


@pytest.fixture
def client():
    """Create Flask test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ==============================================================================
# Group 1: Healthcheck Endpoints (Tests 1 - 7)
# ==============================================================================

def test_health_status_code(client):
    """Test 1: Verify GET /health returns HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_json_keys(client):
    """Test 2: Verify GET /health response contains required operational keys."""
    response = client.get("/health")
    data = response.get_json()
    assert set(data.keys()) == {"status", "service", "uptime", "version"}


def test_health_service_name(client):
    """Test 3: Verify GET /health reports correct service designation."""
    response = client.get("/health")
    data = response.get_json()
    assert data["service"] == "Employee Directory Service"


def test_health_status_value(client):
    """Test 4: Verify GET /health reports status 'OK'."""
    response = client.get("/health")
    data = response.get_json()
    assert data["status"] == "OK"


def test_health_uptime_value(client):
    """Test 5: Verify GET /health reports uptime 'healthy'."""
    response = client.get("/health")
    data = response.get_json()
    assert data["uptime"] == "healthy"


def test_health_version_value(client):
    """Test 6: Verify GET /health returns semantic version 1.0.0."""
    response = client.get("/health")
    data = response.get_json()
    assert data["version"] == "1.0.0"


def test_health_content_type(client):
    """Test 7: Verify GET /health responds with application/json header."""
    response = client.get("/health")
    assert "application/json" in response.content_type


# ==============================================================================
# Group 2: GET /items Basic Retrieval & Roster Schema (Tests 8 - 12)
# ==============================================================================

def test_get_items_status_code(client):
    """Test 8: Verify GET /items returns HTTP 200 OK."""
    response = client.get("/items")
    assert response.status_code == 200


def test_get_items_is_list(client):
    """Test 9: Verify GET /items response is a JSON list."""
    response = client.get("/items")
    data = response.get_json()
    assert isinstance(data, list)


def test_get_items_seed_count(client):
    """Test 10: Verify GET /items returns 4 initialized seed records."""
    response = client.get("/items")
    data = response.get_json()
    assert len(data) == 4


def test_get_items_required_fields(client):
    """Test 11: Verify each employee contains required schema properties."""
    response = client.get("/items")
    data = response.get_json()
    required_fields = {"id", "name", "role", "department", "email", "status"}
    for emp in data:
        assert required_fields.issubset(emp.keys())


def test_get_items_contains_r3_engineer(client):
    """Test 12: Verify R3 (Shaikh Zaid Matinuddin) is present in directory."""
    response = client.get("/items")
    data = response.get_json()
    names = [e["name"] for e in data]
    assert "SHAIKH ZAID MATINUDDIN" in names


# ==============================================================================
# Group 3: GET /items Query Filtering & Search (Tests 13 - 24)
# ==============================================================================

def test_get_items_filter_department_exact(client):
    """Test 13: Verify exact department filtering for 'Platform & Cloud'."""
    response = client.get("/items", query_string={"department": "Platform & Cloud"})
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "SHAIKH RAHMAT"


def test_get_items_filter_department_core_infrastructure(client):
    """Test 14: Verify department filtering for 'Core Infrastructure' returns 2 records."""
    response = client.get("/items", query_string={"department": "Core Infrastructure"})
    data = response.get_json()
    assert len(data) == 2


def test_get_items_filter_department_case_insensitive(client):
    """Test 15: Verify case-insensitive department filtering."""
    response = client.get("/items", query_string={"department": "ai & data science"})
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "YADGIR ZUVERIA SALIM"


def test_get_items_filter_department_all(client):
    """Test 16: Verify department='All' returns complete roster."""
    response = client.get("/items?department=All")
    data = response.get_json()
    assert len(data) == 4


def test_get_items_filter_department_nonexistent(client):
    """Test 17: Verify non-existent department returns empty list."""
    response = client.get("/items?department=NonExistentDept")
    data = response.get_json()
    assert data == []


def test_get_items_search_name_exact(client):
    """Test 18: Verify exact full name search matches single employee."""
    response = client.get("/items?search=SHAIKH ZAID MATINUDDIN")
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == 3


def test_get_items_search_name_partial(client):
    """Test 19: Verify partial name search matches multiple records."""
    response = client.get("/items?search=Zaid")
    data = response.get_json()
    assert len(data) == 2


def test_get_items_search_case_insensitive(client):
    """Test 20: Verify search query is case-insensitive."""
    response = client.get("/items?search=zuveria")
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "YADGIR ZUVERIA SALIM"


def test_get_items_search_email(client):
    """Test 21: Verify search matching email domain substring."""
    response = client.get("/items?search=student.college.edu")
    data = response.get_json()
    assert len(data) == 4


def test_get_items_search_no_match(client):
    """Test 22: Verify search with no matches returns empty array."""
    response = client.get("/items?search=NonExistentUserXYZ")
    data = response.get_json()
    assert data == []


def test_get_items_search_empty_query(client):
    """Test 23: Verify search with empty string returns full roster."""
    response = client.get("/items?search=")
    data = response.get_json()
    assert len(data) == 4


def test_get_items_combined_department_and_search(client):
    """Test 24: Verify simultaneous department and search filtering."""
    response = client.get("/items", query_string={"department": "Core Infrastructure", "search": "MATINUDDIN"})
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == 3


# ==============================================================================
# Group 4: POST /items Employee Registration & Validation (Tests 25 - 32)
# ==============================================================================

def test_add_item_success_status(client):
    """Test 25: Verify POST /items with valid payload returns HTTP 201 Created."""
    payload = {
        "name": "Aarav Sharma",
        "role": "Site Reliability Engineer",
        "department": "Infrastructure",
        "email": "aarav.sharma@enterprise.internal"
    }
    response = client.post("/items", json=payload)
    assert response.status_code == 201


def test_add_item_returns_created_employee(client):
    """Test 26: Verify POST /items returns created employee object."""
    payload = {
        "name": "Priya Nair",
        "role": "QA Automation Lead",
        "department": "Quality Assurance",
        "email": "priya.nair@enterprise.internal"
    }
    response = client.post("/items", json=payload)
    data = response.get_json()
    assert data["name"] == "Priya Nair"
    assert data["role"] == "QA Automation Lead"
    assert data["status"] == "Active"


def test_add_item_persisted_in_store(client):
    """Test 27: Verify created employee is persisted in subsequent GET /items."""
    payload = {
        "name": "Karan Mehra",
        "role": "Security Analyst",
        "department": "DevSecOps",
        "email": "karan.mehra@enterprise.internal"
    }
    client.post("/items", json=payload)
    response = client.get("/items")
    data = response.get_json()
    assert any(e["name"] == "Karan Mehra" for e in data)
    assert len(data) == 5


def test_add_item_auto_generated_email(client):
    """Test 28: Verify omitting email generates enterprise fallback address."""
    payload = {
        "name": "Vikram Patel",
        "role": "Backend Engineer",
        "department": "Platform & Cloud"
    }
    response = client.post("/items", json=payload)
    data = response.get_json()
    assert data["email"] == "vikram.patel@enterprise.internal"


def test_add_item_default_department(client):
    """Test 29: Verify omitting department defaults to 'Engineering'."""
    payload = {
        "name": "Aditi Roy",
        "role": "Data Analyst"
    }
    response = client.post("/items", json=payload)
    data = response.get_json()
    assert data["department"] == "Engineering"


def test_add_item_missing_name_error(client):
    """Test 30: Verify omitting 'name' returns HTTP 400 Bad Request."""
    payload = {"role": "DevOps Engineer"}
    response = client.post("/items", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "name" in data["error"]


def test_add_item_missing_role_error(client):
    """Test 31: Verify omitting 'role' returns HTTP 400 Bad Request."""
    payload = {"name": "Test User"}
    response = client.post("/items", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "role" in data["error"]


def test_add_item_empty_string_validation(client):
    """Test 32: Verify empty or whitespace name returns HTTP 400 Bad Request."""
    payload = {"name": "   ", "role": "   "}
    response = client.post("/items", json=payload)
    assert response.status_code == 400


# ==============================================================================
# Group 5: Payload Security & Prometheus Telemetry (Tests 33 - 35)
# ==============================================================================

def test_add_item_invalid_json_body(client):
    """Test 33: Verify invalid non-JSON body returns HTTP 400 Bad Request."""
    response = client.post(
        "/items",
        data="not-a-json-payload",
        content_type="text/plain"
    )
    assert response.status_code == 400


def test_metrics_endpoint_status_code(client):
    """Test 34: Verify GET /metrics returns HTTP 200 OK."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_and_telemetry(client):
    """Test 35: Verify GET /metrics exposes OpenMetrics telemetry format."""
    # Issue a health request first to trigger counters
    client.get("/health")
    response = client.get("/metrics")
    content = response.data.decode("utf-8")
    assert response.status_code == 200
    assert "http_requests_total" in content
    assert "python_info" in content
