#!/usr/bin/env bash
# Creates a clean, meaningful commit history (16 commits) for the M3 requirement.
# Run ONCE from the repo root, before your first push:
#   ./scripts/git-bootstrap.sh
# Afterwards: git remote add origin <your repo URL> && git push -u origin main
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -d .git ]; then echo "A git repo already exists here; aborting."; exit 1; fi
git init -q -b main
git config user.name >/dev/null || { echo "Set your identity first: git config --global user.name / user.email"; exit 1; }

commit() { # commit "message" path...
  local msg="$1"; shift
  git add -- "$@"
  git commit -q -m "$msg"
  echo "committed: $msg"
}

commit "chore: add gitignore and env example" .gitignore .env.example
commit "feat(backend): add database config and ORM models for doctors, patients and appointments" \
  backend/app/__init__.py backend/app/database.py backend/app/models.py
commit "feat(backend): add Alembic migrations for core tables and appointment indexes" \
  backend/alembic.ini backend/alembic
commit "feat(backend): add request schemas and Prometheus business metrics" \
  backend/app/schemas.py backend/app/metrics.py
commit "feat(backend): add doctors and patients REST endpoints" \
  backend/app/routers/__init__.py backend/app/routers/doctors.py backend/app/routers/patients.py
commit "feat(backend): add appointments, live queue, stats, health, ready and metrics endpoints" \
  backend/app/routers/appointments.py backend/app/main.py
commit "test(backend): add pytest suite using an in-memory SQLite database" \
  backend/tests backend/pytest.ini backend/ruff.toml backend/requirements.txt backend/requirements-dev.txt
commit "build(backend): add non-root backend Dockerfile" backend/Dockerfile backend/.dockerignore
commit "feat(frontend): add React dashboard with live queue board and booking modal" \
  frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html frontend/src
commit "build(frontend): add multi-stage Dockerfile with unprivileged Nginx" \
  frontend/Dockerfile frontend/nginx.conf.template frontend/.dockerignore
commit "build: add docker-compose stack and demo seed script" docker-compose.yml scripts/seed.sh
commit "ci: add GitHub Actions pipeline with pytest, Trivy scan and GHCR push" .github
commit "infra: add Terraform for AWS VPC and EKS" terraform
commit "deploy: add Helm chart and namespace manifest" helm k8s
commit "ops: add Prometheus and Grafana configuration and dashboard" monitoring
git add -A
git commit -q -m "docs: add README, troubleshooting labs and local cluster scripts"
echo "committed: docs: add README, troubleshooting labs and local cluster scripts"

echo; git log --oneline
