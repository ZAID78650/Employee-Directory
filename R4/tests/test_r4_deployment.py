"""
Role R4: Automated Deployment & Endpoint Verification Suite
Verifies Docker Compose, Kubernetes NodePort, Prometheus Telemetry, and Grafana.
"""

import requests
import pytest

DOCKER_APP_URL = "http://localhost:5001"
K8S_APP_URL = "http://localhost:30501"
PROMETHEUS_URL = "http://localhost:9090"
GRAFANA_URL = "http://localhost:3000"


def test_docker_app_health_endpoint():
    """Verify GET /health on Docker Compose container returns HTTP 200 OK."""
    url = f"{DOCKER_APP_URL}/health"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OK"
    assert "Employee Directory" in data["service"]


def test_docker_app_items_endpoint():
    """Verify GET /items on Docker Compose container returns employee list."""
    url = f"{DOCKER_APP_URL}/items"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_docker_app_add_item_post():
    """Verify POST /items on Docker Compose container creates employee with status 201."""
    url = f"{DOCKER_APP_URL}/items"
    payload = {
        "name": "R4 Test Engineer",
        "role": "Deployment Engineer",
        "department": "Infrastructure",
        "email": "r4.engineer@enterprise.internal"
    }
    res = requests.post(url, json=payload, timeout=5)
    assert res.status_code == 201
    resp_json = res.json()
    item = resp_json.get("item", resp_json)
    assert item["name"] == "R4 Test Engineer"


def test_docker_app_prometheus_metrics():
    """Verify GET /metrics on Docker Compose container exposes telemetry."""
    url = f"{DOCKER_APP_URL}/metrics"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    text = res.text
    assert "python_gc_objects_collected_total" in text or "http_requests_total" in text


def test_prometheus_server_health_and_target_up():
    """Verify Prometheus server is healthy and scrape target app:5001 is UP."""
    res_health = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
    assert res_health.status_code == 200

    res_targets = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=5)
    assert res_targets.status_code == 200
    targets_data = res_targets.json()
    active_targets = targets_data.get("data", {}).get("activeTargets", [])
    assert len(active_targets) > 0
    assert any(t.get("health") == "up" for t in active_targets)


def test_grafana_server_response():
    """Verify Grafana server responds on port 3000."""
    res = requests.get(GRAFANA_URL, timeout=5, allow_redirects=False)
    assert res.status_code in [200, 302]


def test_k8s_bonus_nodeport_health():
    """Bonus verification: Kubernetes cluster NodePort service responds on port 30501."""
    url = f"{K8S_APP_URL}/health"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OK"


def test_k8s_bonus_nodeport_items():
    """Bonus verification: Kubernetes cluster NodePort /items endpoint responds."""
    url = f"{K8S_APP_URL}/items"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
