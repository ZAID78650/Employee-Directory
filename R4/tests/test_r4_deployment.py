"""
Role R4: Automated Deployment & Endpoint Verification Suite
Verifies Docker Compose, Kubernetes NodePort, Prometheus Telemetry, and Grafana.
Gracefully skips if external containers are not running in environment (e.g. GitHub Actions runner).
"""

import os
import requests
import pytest

DOCKER_APP_URL = os.environ.get("DOCKER_APP_URL", "http://localhost:5001")
K8S_APP_URL = os.environ.get("K8S_APP_URL", "http://localhost:30501")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")


def is_service_reachable(url, timeout=1.0):
    """Checks if a target URL is reachable without raising an unhandled exception."""
    try:
        res = requests.get(url, timeout=timeout)
        return True
    except Exception:
        return False


def test_docker_app_health_endpoint():
    """Verify GET /health on Docker Compose container returns HTTP 200 OK."""
    if not is_service_reachable(f"{DOCKER_APP_URL}/health"):
        pytest.skip("Docker Compose application container is not running on :5001 (skipping in CI environment)")

    url = f"{DOCKER_APP_URL}/health"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OK"
    assert "Employee Directory" in data["service"]


def test_docker_app_items_endpoint():
    """Verify GET /items on Docker Compose container returns employee list."""
    if not is_service_reachable(f"{DOCKER_APP_URL}/items"):
        pytest.skip("Docker Compose application container is not running on :5001")

    url = f"{DOCKER_APP_URL}/items"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_docker_app_add_item_post():
    """Verify POST /items on Docker Compose container creates employee with status 201."""
    if not is_service_reachable(f"{DOCKER_APP_URL}/items"):
        pytest.skip("Docker Compose application container is not running on :5001")

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
    if not is_service_reachable(f"{DOCKER_APP_URL}/metrics"):
        pytest.skip("Docker Compose application container is not running on :5001")

    url = f"{DOCKER_APP_URL}/metrics"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    text = res.text
    assert "python_gc_objects_collected_total" in text or "http_requests_total" in text


def test_prometheus_server_health_and_target_up():
    """Verify Prometheus server is healthy and scrape target app:5001 is UP."""
    if not is_service_reachable(f"{PROMETHEUS_URL}/-/healthy"):
        pytest.skip("Prometheus server is not running on :9090 (skipping in CI environment)")

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
    if not is_service_reachable(GRAFANA_URL):
        pytest.skip("Grafana server is not running on :3000 (skipping in CI environment)")

    res = requests.get(GRAFANA_URL, timeout=5, allow_redirects=False)
    assert res.status_code in [200, 302]


def test_k8s_bonus_nodeport_health():
    """Bonus verification: Kubernetes cluster NodePort service responds on port 30501."""
    if not is_service_reachable(f"{K8S_APP_URL}/health"):
        pytest.skip("Kubernetes NodePort is not reachable on :30501 (skipping in CI environment)")

    url = f"{K8S_APP_URL}/health"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OK"


def test_k8s_bonus_nodeport_items():
    """Bonus verification: Kubernetes cluster NodePort /items endpoint responds."""
    if not is_service_reachable(f"{K8S_APP_URL}/items"):
        pytest.skip("Kubernetes NodePort is not reachable on :30501 (skipping in CI environment)")

    url = f"{K8S_APP_URL}/items"
    res = requests.get(url, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

