"""ClinicQ API — clinic appointment and queue management."""

from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import appointments, doctors, patients

app = FastAPI(
    title="ClinicQ API",
    description="Clinic appointment booking and live queue management.",
    version="1.0.0",
)

app.include_router(doctors.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
# stats lives on the appointments router; queue has its own router
app.include_router(appointments.router, prefix="/api")
app.include_router(appointments.queue_router, prefix="/api")


@app.get("/", tags=["meta"])
def root():
    return {"service": "clinicq-api", "version": app.version, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    """Liveness: the process is up."""
    return {"status": "OK"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    """Readiness: the database answers, so we can serve traffic."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "READY"}


Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, include_in_schema=False
)
