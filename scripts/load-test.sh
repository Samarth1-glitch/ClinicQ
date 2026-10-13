#!/usr/bin/env bash
# Generate CPU load on the backend from inside the cluster so the HPA scales it up.
# Watch in a second terminal:  kubectl get hpa -n clinicq -w
# Stop with Ctrl+C (the load pod is deleted automatically).
set -euo pipefail

NAMESPACE="${NAMESPACE:-clinicq}"
TARGET="${TARGET:-http://clinicq-backend:8000/api/appointments/stats}"
WORKERS="${WORKERS:-8}"

echo "Hitting $TARGET with $WORKERS parallel loops ..."
kubectl run load-generator -n "$NAMESPACE" --rm -i --restart=Never --image=busybox:1.36 -- \
  /bin/sh -c "for i in \$(seq $WORKERS); do (while true; do wget -q -O- $TARGET >/dev/null; done) & done; wait"
