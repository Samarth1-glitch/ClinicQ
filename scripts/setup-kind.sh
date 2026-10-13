#!/usr/bin/env bash
# One-shot FREE local Kubernetes environment: kind + ingress-nginx + metrics-server
# + Prometheus/Grafana + the ClinicQ Helm chart.
# Requires: docker, kind, kubectl, helm.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Creating kind cluster"
kind create cluster --name clinicq --config scripts/kind-config.yaml

echo "==> Installing ingress-nginx"
kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s

echo "==> Installing metrics-server (needed by the HPA)"
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system \
  --set 'args={--kubelet-insecure-tls}'

echo "==> Building and loading images"
docker build -t clinicq-backend:local ./backend
docker build -t clinicq-frontend:local ./frontend
kind load docker-image clinicq-backend:local clinicq-frontend:local --name clinicq

echo "==> Installing Prometheus + Grafana"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml
kubectl wait --for condition=established --timeout=120s crd/servicemonitors.monitoring.coreos.com
kubectl apply -f monitoring/dashboard-configmap.yaml

echo "==> Deploying ClinicQ"
kubectl apply -f k8s/namespace.yaml
helm upgrade --install clinicq ./helm/clinicq -n clinicq -f helm/clinicq/values-dev.yaml --wait --timeout 5m

cat <<'EOF'

Done. Next steps:
  1. Add this line to your hosts file (/etc/hosts, or C:\Windows\System32\drivers\etc\hosts):
       127.0.0.1 clinicq.local
  2. Open http://clinicq.local
  3. Seed demo data:       ./scripts/seed.sh http://clinicq.local
  4. Grafana:              kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80   (admin / clinicq-admin)
  5. Prometheus targets:   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090
  6. Delete everything:    kind delete cluster --name clinicq
EOF
