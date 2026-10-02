# Employee Directory - End-to-End DevOps Pipeline

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](https://github.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)](https://www.docker.com)
[![Prometheus](https://img.shields.io/badge/Metrics-Prometheus-E6522C)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Monitoring-Grafana-F46800)](https://grafana.com)

**Agile Software Development & DevOps Lab (2015119) | Practical 10**  
**Group:** Batch B3 - Group B3-G3  
**Project Topic:** Employee Directory

---

## 👥 Group Members & Roles

- **Roll 67 (R1)**: Agile Planner & Documentation Lead (Jira Project, Epic, Stories, Sprint)
- **Roll 56 (R2)**: Developer & Version Control (Flask REST App, Unit Tests, Git PR)
- **Roll 60 (R3)**: CI/CD & Containerization Engineer (GitHub Actions, Dockerfile, Docker Hub)
- **Roll 61 (R4)**: Deployment & Monitoring Engineer (Docker Compose, Prometheus, Grafana)

---

## 🚀 Quick Start

### 1. Run Application Locally (Python)
```bash
# Install dependencies
pip install -r requirements.txt

# Run Unit Tests (5 passed)
pytest -v

# Start Application Server
python app.py
```
Open [http://localhost:5001](http://localhost:5001) in your browser.

---

### 2. Run with Docker Compose (App + Prometheus + Grafana)
```bash
docker compose up --build -d
```

| Service | URL | Description | Credentials |
| :--- | :--- | :--- | :--- |
| **Employee Directory UI** | [http://localhost:5001](http://localhost:5001) | Main Web Dashboard | None |
| **REST API - Health** | [http://localhost:5001/health](http://localhost:5001/health) | Healthcheck endpoint | None |
| **REST API - Items** | [http://localhost:5001/items](http://localhost:5001/items) | JSON Employee records | None |
| **Prometheus Metrics** | [http://localhost:5001/metrics](http://localhost:5001/metrics) | Telemetry scrape target | None |
| **Prometheus Dashboard** | [http://localhost:9090](http://localhost:9090) | Scrape targets & metrics query | None |
| **Grafana Dashboard** | [http://localhost:3000](http://localhost:3000) | Visual monitoring dashboard | admin / admin |

---

## 📡 API Endpoints

- `GET /health` -> Returns `{"status": "OK", "service": "Employee Directory Service", "uptime": "healthy"}`
- `GET /items` -> Returns list of employees (supports `?search=` and `?department=`)
- `POST /items` -> Adds a new employee (`{"name": "...", "role": "...", "department": "..."}`)
- `GET /items/<id>` -> Retrieve single employee
- `DELETE /items/<id>` -> Delete employee
- `GET /metrics` -> Exposes Prometheus client telemetry

---

## 🧪 Testing

```bash
pytest -v
```
All unit tests verify endpoint availability, response status codes, JSON payload schema, validation rules, and Prometheus counters.
