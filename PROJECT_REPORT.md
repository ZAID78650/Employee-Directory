# Practical 10: End-to-End DevOps Pipeline Report
**Course:** Agile Software Development & DevOps Lab (2015119) | TE AI&DS  
**Group:** Batch B3 - Group B3-G3  
**Project Topic:** Employee Directory Management System  
**Pipeline Flow:** Jira (Plan) &rarr; Git/GitHub (Code) &rarr; GitHub Actions (Build + Test) &rarr; Docker (Package) &rarr; Docker Hub (Release) &rarr; Docker Compose (Deploy) &rarr; Prometheus + Grafana (Monitor)

---

## 1. Group Members & Role Allocations

| Role | Roll No | Name / Title | Assigned Responsibility | Deliverable Produced |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | **Roll 67** | Agile Planner & Documentation Lead | Setup Jira Project, Epic, 3 User Stories, Sprint management, Issue keys linking, Report compilation | Jira Board, Backlog & Sprint Screenshots, Final Lab Report |
| **R2** | **Roll 56** | Developer & Version Control | REST Application (`app.py`), Pytest test suite (`test_app.py`), Git feature branching & Pull Request merge | Tested Flask REST API, GitHub repo commit history |
| **R3** | **Roll 60** | CI/CD & Containerization Engineer | GitHub Actions CI/CD workflow (`ci-cd.yml`), Dockerfile, Automated testing & Docker Hub publishing | Passing CI pipeline, Docker image packaging |
| **R4** | **Roll 61** | Deployment & Monitoring Engineer | Docker Compose orchestration (`docker-compose.yml`), Prometheus scrape config (`prometheus.yml`), Grafana Dashboard provisioning | Live multi-container deployment, Metrics dashboard |

---

## 2. System Architecture & DevOps Pipeline

```
+---------------------------------------------------------------------------------------------------------+
|                                        DEVOPS LIFECYCLE (B3-G3)                                         |
+---------------------------------------------------------------------------------------------------------+

  [ 1. PLAN ]               [ 2. CODE & VERSION CONTROL ]          [ 3. CI / AUTOMATED TEST ]
  Jira Software             Git & GitHub                           GitHub Actions
  +------------------+      +------------------------------+       +-----------------------------+
  | Epic: EMP-100    | ---> | Feature Branch:              | ----> | - Setup Python 3.10         |
  | Stories:         |      | feature/EMP-102-rest-endpts  |       | - Install requirements.txt  |
  | EMP-101,102,103  |      | PR #1 merged to 'main'       |       | - Run pytest -v (5 passed)  |
  +------------------+      +------------------------------+       +-----------------------------+
                                                                                  |
                                                                                  v
  [ 6. MONITOR ]             [ 5. DEPLOY ]                         [ 4. PACKAGE & RELEASE ]
  Prometheus & Grafana       Docker Compose                        Docker & Docker Hub
  +------------------+      +------------------------------+       +-----------------------------+
  | Prometheus :9090 | <--- | Multi-Container Stack:       | <---- | Multi-stage Docker image    |
  | (Scrapes /metrics|      | 1. App (:5001)               |       | employee-directory:latest   |
  | Grafana :3000    |      | 2. Prometheus (:9090)        |       | Pushed to Docker Hub        |
  | (Visual Panels)  |      | 3. Grafana (:3000)           |       |                             |
  +------------------+      +------------------------------+       +-----------------------------+
```

---

## 3. Application Specification & Endpoints

The core service is a lightweight, responsive Flask application with in-memory persistence designed for rapid end-to-end DevOps automation.

### Verified Endpoints:
1. **`GET /health`** (Mandatory Monitoring Endpoint):
   - **Response:** `{"status": "OK", "service": "Employee Directory Service", "uptime": "healthy", "version": "1.0.0"}`
   - **Status Code:** `200 OK`
2. **`GET /items`** (Mandatory Topic Endpoint):
   - Returns JSON list of all active employee records.
   - Supports search and department filtering.
   - **Status Code:** `200 OK`
3. **`POST /items`** (Mandatory Topic Endpoint):
   - Accepts payload: `{"name": "...", "role": "...", "department": "...", "email": "...", "status": "..."}`
   - Adds employee to the in-memory registry.
   - **Status Code:** `201 Created`
4. **`GET /metrics`** (Telemetry / Scrape Target):
   - Exposes Prometheus client gauges, counters (`http_requests_total`), and histograms (`http_request_duration_seconds`).
5. **`GET /`** (Web Frontend):
   - Interactive, production-grade Tailwind CSS dashboard for live employee directory searching, adding, and health status indicators.

---

## 4. Jira Project Planning (Role R1)

- **Project Key:** `EMP`
- **Epic:** `EMP-100: End-to-End Employee Directory DevOps Pipeline`
- **Sprint:** `Sprint 1 - Minimum Viable Deployment`
- **User Stories:**
  - `EMP-101`: *As an HR Lead, I want a health check endpoint so uptime monitoring systems can verify operational status.* (GET `/health`)
  - `EMP-102`: *As a Department Manager, I want to retrieve the directory of all employees so I can view team members.* (GET `/items`)
  - `EMP-103`: *As an Administrator, I want to add new personnel to the employee directory.* (POST `/items`)
- **Traceability:** Every git commit message contains the Jira issue key (e.g. `EMP-101: Initial setup...`, `EMP-102: Implement endpoints...`, `EMP-103: Merge pull request #1...`).

---

## 5. Automated CI/CD Pipeline (Role R3)

Configured under `.github/workflows/ci-cd.yml`:
1. Triggers automatically on push to `main` and all `feature/*` branches, as well as Pull Requests.
2. **Build and Test Job:**
   - Checks out repo via `actions/checkout@v4`.
   - Provisions Python runtime via `actions/setup-python@v5`.
   - Executes automated testing with `pytest -v`.
3. **Docker Build & Push Job:**
   - Runs upon merge to `main`.
   - Uses `docker/build-push-action@v5`.
   - Securely accesses Docker Hub credentials via `secrets.DOCKERHUB_USERNAME` and `secrets.DOCKERHUB_TOKEN` (Zero hardcoded secrets, DevSecOps compliance).

---

## 6. Container Orchestration & Monitoring (Role R4 & R5)

Orchestrated using `docker-compose.yml`:
1. **Service `app`:** Runs containerized Flask app on port `5001`. Includes internal docker healthcheck.
2. **Service `prometheus`:** Runs `prom/prometheus:latest` on port `9090`. Configured via `prometheus.yml` to scrape `app:5001/metrics` every 5 seconds.
3. **Service `grafana`:** Runs `grafana/grafana:latest` on port `3000`. Auto-provisions:
   - Prometheus Data Source (`datasource.yml`)
   - Pre-configured dashboard (`employee_dashboard.json`) rendering:
     - Total HTTP Requests timeseries by route and method (`http_requests_total`)
     - Service Health status panel (`up{job="employee-directory-service"}`)

---

## 7. Viva Questions & Model Answers

### Q1 (For R1): What is the difference between an Epic and a User Story in Agile?
> **Answer:** An **Epic** represents a large body of work or a high-level capability that cannot be completed within a single sprint (e.g., "Build the End-to-End DevOps Pipeline"). A **User Story** is a smaller, self-contained functional requirement derived from the Epic written from the end-user's perspective (e.g., "GET /items to view employees"), small enough to be designed, coded, tested, and accepted within a single sprint.

### Q2 (For R2): What is a Pull Request (PR) and why do we use branches?
> **Answer:** A **branch** isolates changes from the main production code (`main`), allowing developers to work on features concurrently without introducing breaking changes or instability. A **Pull Request** is a peer-review mechanism where changes from a feature branch are formally proposed, reviewed, tested via automated CI checks, and approved before being merged into the target branch.

### Q3 (For R3): What does the CI workflow file do and why do we use GitHub Secrets?
> **Answer:** The CI workflow file (`ci-cd.yml`) defines automated steps (triggers, checkout, environment setup, dependency installation, and testing) that execute in an isolated virtual runner on code push. We use **GitHub Secrets** to securely inject sensitive credentials (like Docker Hub tokens or API keys) into runner environment variables during execution without exposing them in plaintext inside source control (DevSecOps).

### Q4 (For R4): What is the purpose of Docker Compose?
> **Answer:** Docker Compose is an orchestration tool used to define and run multi-container Docker applications using a declarative YAML file. It coordinates networking, storage volumes, environment variables, dependencies (`depends_on`), and service startup order across multiple isolated containers (such as App + Prometheus + Grafana) with a single command (`docker compose up`).

### Q5 (For R5): What is a Prometheus exporter / scrape target?
> **Answer:** A Prometheus **scrape target** is an HTTP endpoint (typically `/metrics`) exposed by an application that presents telemetry data in Prometheus text format. An **exporter** or client library translates internal application metrics (counters, gauges, response durations) into this format so Prometheus can poll and store them periodically as time-series data.

---

## 8. Conclusion
The B3-G3 Employee Directory DevOps project demonstrates a complete implementation of modern Agile and DevOps practices: traceable planning with Jira, version control with Git branching and Pull Requests, continuous integration with Pytest and GitHub Actions, containerization with Docker, multi-service orchestration with Docker Compose, and observability with Prometheus and Grafana.
