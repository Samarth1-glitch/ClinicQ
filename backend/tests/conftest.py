"""Shared fixtures. Tests always run against an in-memory SQLite DB, never PostgreSQL."""

import os

# Must be set before app.database is imported so no real DB URL is ever used in tests.
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def doctor(client):
    resp = client.post(
        "/api/doctors",
        json={"name": "Dr. Asha Rao", "specialization": "General Medicine", "room": "101"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def patient(client):
    resp = client.post(
        "/api/patients", json={"name": "Ravi Kumar", "phone": "9876543210", "age": 34}
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def today_slot():
    """A time today, rounded to the minute, as an ISO string (helper factory)."""
    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    def make(offset_minutes: int = 0) -> str:
        return (base + timedelta(minutes=offset_minutes)).isoformat()

    return make
