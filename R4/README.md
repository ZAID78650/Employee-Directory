# Role R4: Deployment & Observability Operations Guide
**Practical 10: End-to-End DevOps Pipeline**  
**Course:** Agile Software Development & DevOps Lab (2015119) | TE AI&DS  
**Batch & Group:** Batch B3 - Group B3-G3 (Employee Directory)  
**Role Title:** R4 — Deployment & Monitoring Engineer (Roll 61)  

---

## 1. Role Mandate & Deliverables
As **Role R4**, the primary engineering objectives are:
1. Pull the container image built and pushed by Role R3 (`employee-directory:latest`).
2. Orchestrate and run the multi-container application stack using `docker-compose.yml`.
3. Verify all mandatory REST endpoints and frontend routes live in the browser.
4. Configure Prometheus scrape telemetry and Grafana visualization panels.
5. **Bonus Challenge:** Deploy the containerized application on a local Kubernetes / Minikube cluster using declarative YAML manifests.

---

## 2. Directory Structure (`R4/`)
```
R4/
├── docker-compose.yml           # Multi-container orchestration (App, Prometheus, Grafana)
├── prometheus.yml               # Scrape target config polling app:5001/metrics every 5s
├── README.md                    # Comprehensive R4 operations & test manual
├── k8s/                         # Bonus: Kubernetes / Minikube deployment manifests
│   ├── namespace.yaml           # Dedicated 'employee-directory' namespace
│   ├── configmap.yaml           # App configuration environment variables
│   ├── deployment.yaml          # Pod replica specification (2 replicas, liveness/readiness probes)
│   └── service.yaml             # NodePort service exposing cluster on port 30501
├── scripts/
│   └── deploy_and_verify.sh     # One-click execution and endpoint health audit script
├── tests/
│   └── test_r4_deployment.py    # Automated Pytest suite asserting 8/8 deployment checks
└── screenshots/                 # High-resolution browser captures of live verified endpoints
    ├── r4_01_docker_compose_app_5001.png       # Live App login/dashboard on port 5001
    ├── r4_02_docker_compose_health.png         # GET /health on port 5001 (Status: 200 OK)
    ├── r4_03_docker_compose_items.png          # GET /items on port 5001 (Status: 200 OK)
    ├── r4_04_k8s_nodeport_health_30501.png     # K8s NodePort GET /health on port 30501
    ├── r4_05_k8s_nodeport_items_30501.png      # K8s NodePort GET /items on port 30501
    ├── r4_06_prometheus_targets_9090.png       # Prometheus Scrape Target UP on port 9090
    └── r4_07_grafana_dashboard_3000.png        # Grafana Operational Dashboard on port 3000
```

---

## 3. Quickstart & Verification Commands

### A. Run Multi-Container Stack (Docker Compose)
```bash
# Inside R4/ directory
docker-compose up -d

# Verify container statuses
docker ps --filter "name=employee-directory"
```

### B. Verify Endpoints in Browser
- **Application Dashboard:** [http://localhost:5001](http://localhost:5001)
- **Health Heartbeat Endpoint:** [http://localhost:5001/health](http://localhost:5001/health) &rarr; `{"status": "OK", "uptime": "healthy"}`
- **Items Roster Endpoint:** [http://localhost:5001/items](http://localhost:5001/items) &rarr; `[{"id": 1, "name": ...}]`
- **Prometheus Telemetry Scraper:** [http://localhost:5001/metrics](http://localhost:5001/metrics)
- **Prometheus Server Targets:** [http://localhost:9090/targets](http://localhost:9090/targets) &rarr; Target `app:5001` is **UP (1)**
- **Grafana Visualization Portal:** [http://localhost:3000](http://localhost:3000) &rarr; Credentials: `admin` / `admin`

---

## 4. Bonus: Kubernetes / Minikube Deployment

Deploy the container to the local Kubernetes cluster:
```bash
# Apply all manifests in order
kubectl apply -f R4/k8s/namespace.yaml
kubectl apply -f R4/k8s/configmap.yaml
kubectl apply -f R4/k8s/deployment.yaml
kubectl apply -f R4/k8s/service.yaml

# Verify pod status and replicas
kubectl get pods -n employee-directory -o wide

# Test NodePort endpoint directly
curl -s http://localhost:30501/health
curl -s http://localhost:30501/items
```

---

## 5. Automated Verification Results (Pytest 8/8 Passed)
Execute the automated test suite from the root directory:
```bash
pytest R4/tests/test_r4_deployment.py -v
```
**Test Results:**
```
R4/tests/test_r4_deployment.py::test_docker_app_health_endpoint PASSED        [ 12%]
R4/tests/test_r4_deployment.py::test_docker_app_items_endpoint PASSED         [ 25%]
R4/tests/test_r4_deployment.py::test_docker_app_add_item_post PASSED          [ 37%]
R4/tests/test_r4_deployment.py::test_docker_app_prometheus_metrics PASSED      [ 50%]
R4/tests/test_r4_deployment.py::test_prometheus_server_health_and_target_up PASSED [ 62%]
R4/tests/test_r4_deployment.py::test_grafana_server_response PASSED           [ 75%]
R4/tests/test_r4_deployment.py::test_k8s_bonus_nodeport_health PASSED         [ 87%]
R4/tests/test_r4_deployment.py::test_k8s_bonus_nodeport_items PASSED          [100%]

============================== 8 passed in 0.14s ===============================
```
