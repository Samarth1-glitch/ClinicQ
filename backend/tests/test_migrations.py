"""Run the real Alembic migrations against a throw-away SQLite file."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parent.parent


def test_migrations_upgrade_and_downgrade(tmp_path, monkeypatch):
    db_file = tmp_path / "migrations.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))

    command.upgrade(cfg, "head")
    inspector = inspect(create_engine(f"sqlite:///{db_file}"))
    assert {"doctors", "patients", "appointments"} <= set(inspector.get_table_names())
    index_names = {i["name"] for i in inspector.get_indexes("appointments")}
    assert "ix_appointments_doctor_scheduled" in index_names

    command.downgrade(cfg, "base")
    inspector = inspect(create_engine(f"sqlite:///{db_file}"))
    assert "appointments" not in inspector.get_table_names()
