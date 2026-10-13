# ClinicQ — Clinic Appointments & Live Queue

ClinicQ is a small SaaS-style application for a clinic front desk. Reception staff register doctors and
patients, book appointments, check patients in as they arrive, and watch a **live queue board** that shows
who is being served next for each doctor. Every booking gets a per-doctor, per-day **token number**, and a
doctor's time slot can never be double-booked.

The project also demonstrates the full DevOps path from laptop to a monitored Kubernetes cluster.

```
Developer -> Git/GitHub -> GitHub Actions (ruff, pytest, frontend build, Docker build,
                           Trivy scan, push to GHCR with commit-SHA tags)
                                   |
          Terraform -> AWS VPC + EKS -> Helm -> Ingress -> Frontend (Nginx) / Backend (FastAPI) -> PostgreSQL
                                                                   |
                                                       Prometheus -> Grafana
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, responsive CSS, served by unprivileged Nginx |
| Backend | FastAPI, SQLAlchemy 2, Alembic migrations, Pydantic |
| Database | PostgreSQL 16 |
| Tests | pytest (in-memory SQLite test DB), ruff |
| Containers | Docker (non-root), Docker Compose |
| CI/CD | GitHub Actions, Trivy, GitHub Container Registry |
| Infrastructure | Terraform (AWS VPC + EKS), Kubernetes, Helm, Ingress, HPA |
| Observability | Prometheus, Grafana, `/health`, `/ready`, `/metrics` |

## Run it locally (one command)

```bash
docker compose up --build
```

- App: http://localhost:3000
- API docs (Swagger): http://localhost:8000/docs
- Health / metrics: http://localhost:8000/health , http://localhost:8000/metrics
- Demo data: `./scripts/seed.sh http://localhost:8000`
- Stop: `docker compose down` (add `-v` to also delete the database volume)

## REST API

| Method | Path | Purpose |
|---|---|---|
| GET / POST | `/api/doctors` | list / create doctors |
| GET / PUT / DELETE | `/api/doctors/{id}` | read / update / delete a doctor |
| GET / POST | `/api/patients` | list (search with `?q=`) / create patients |
| GET / PUT / DELETE | `/api/patients/{id}` | read / update / delete a patient |
| GET / POST | `/api/appointments` | list (filter by `date`, `doctor_id`, `status`) / book |
| GET / PUT / DELETE | `/api/appointments/{id}` | read / change status or time / delete |
| GET | `/api/appointments/stats` | today's KPIs |
| GET | `/api/queue` | today's waiting patients, numbered per doctor |
| GET | `/health`, `/ready`, `/metrics` | liveness, readiness (checks DB), Prometheus metrics |

Appointment status flow: `booked → checked_in → completed`, or `cancelled` from `booked`/`checked_in`.
Completed and cancelled appointments are final.

Custom business metrics (next to the default HTTP metrics): `clinicq_appointments_booked_total`,
`clinicq_appointments_cancelled_total`.

## Develop the backend without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v                     # uses in-memory SQLite, never your real DB
export DATABASE_URL='postgresql+psycopg://clinicq:clinicq@localhost:5432/clinicq'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend: `cd frontend && npm install && npm run dev` (Vite proxies `/api` to `localhost:8000`).

## Repository layout

```
backend/          FastAPI app (app/), tests (tests/), Alembic migrations (alembic/), Dockerfile
frontend/         React + Vite app, Nginx template, multi-stage Dockerfile
docker-compose.yml  Full local stack (frontend + backend + postgres)
terraform/        AWS VPC + EKS
helm/clinicq/     Helm chart (backend, frontend, postgres, ingress, HPA, ServiceMonitor)
k8s/              Namespace manifest
monitoring/       kube-prometheus-stack values + Grafana dashboard
troubleshooting/  Deliberately broken manifests for the live debugging labs
scripts/          seed data, load test, local kind cluster setup
.github/workflows/  CI/CD pipeline
docs/             Step-by-step guide
```

## CI/CD

On every push to `main` the pipeline runs `ruff` + `pytest`, builds the React app, builds both Docker images
tagged with the **commit SHA**, scans them with **Trivy** (fails on HIGH/CRITICAL), and pushes them to GHCR.
Terraform and the Helm chart are validated on every run. An optional deploy job runs `helm upgrade --install`
on EKS when the repository variable `DEPLOY_ENABLED` is `true`.

See [docs/STEP_BY_STEP.md](docs/STEP_BY_STEP.md) for the full walkthrough, including the low-cost AWS plan.
