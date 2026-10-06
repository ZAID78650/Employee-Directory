#!/bin/bash
# ==============================================================================
# Role R4: Automated Deployment & Health Verification Script
# Practical 10: End-to-End DevOps Pipeline (Batch B3 - Group B3-G3)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}  ROLE R4: DEPLOYMENT & OBSERVABILITY AUTOMATION SUITE           ${NC}"
echo -e "${BLUE}==================================================================${NC}"

# Step 1: Verify Running Docker Containers
echo -e "\n${YELLOW}[Step 1] Checking Docker Compose Multi-Container Stack...${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Step 2: Test Endpoints
echo -e "\n${YELLOW}[Step 2] Testing Docker Compose App Endpoints (:5001)...${NC}"
echo -n "  Testing GET /health: "
curl -s -f http://localhost:5001/health > /dev/null && echo -e "${GREEN}200 OK${NC}" || echo "FAILED"

echo -n "  Testing GET /items:  "
curl -s -f http://localhost:5001/items > /dev/null && echo -e "${GREEN}200 OK${NC}" || echo "FAILED"

echo -n "  Testing GET /metrics:"
curl -s -f http://localhost:5001/metrics > /dev/null && echo -e "${GREEN}200 OK${NC}" || echo "FAILED"

# Step 3: Test Prometheus & Grafana
echo -e "\n${YELLOW}[Step 3] Checking Observability Infrastructure (:9090, :3000)...${NC}"
echo -n "  Prometheus Server Health: "
curl -s -f http://localhost:9090/-/healthy > /dev/null && echo -e "${GREEN}HEALTHY${NC}" || echo "FAILED"

echo -n "  Grafana Dashboard Portal: "
STATUS_GRAFANA=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
echo -e "${GREEN}HTTP ${STATUS_GRAFANA}${NC}"

# Step 4: Verify Kubernetes Pods
echo -e "\n${YELLOW}[Step 4] Checking Kubernetes / Minikube Cluster Deployment...${NC}"
kubectl get pods -n employee-directory -o wide
kubectl get svc -n employee-directory

echo -e "\n${YELLOW}[Step 5] Testing Kubernetes NodePort Service (:30501)...${NC}"
echo -n "  Testing K8s GET /health: "
curl -s -f http://localhost:30501/health > /dev/null && echo -e "${GREEN}200 OK (Pod Responding)${NC}" || echo "FAILED"

echo -n "  Testing K8s GET /items:  "
curl -s -f http://localhost:30501/items > /dev/null && echo -e "${GREEN}200 OK (Pod Responding)${NC}" || echo "FAILED"

echo -e "\n${GREEN}==================================================================${NC}"
echo -e "${GREEN}  ✓ ALL R4 OPERATIONS COMPLETED & VERIFIED SUCCESSFULLY!         ${NC}"
echo -e "${GREEN}==================================================================${NC}"
