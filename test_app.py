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
