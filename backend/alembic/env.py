"""Alembic environment. The database URL is read from DATABASE_URL."""

import os
from logging.config import fileConfig

from sqlalchemy import create_engine, text

from alembic import context
from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# Arbitrary constant so several replicas starting at once run migrations one at a time.
MIGRATION_LOCK_ID = 727_272


def get_url() -> str:
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_url())
    with engine.connect() as connection:
        is_postgres = connection.dialect.name == "postgresql"
        if is_postgres:
            connection.execute(text(f"SELECT pg_advisory_lock({MIGRATION_LOCK_ID})"))
            connection.commit()

        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

        if is_postgres:
            connection.execute(text(f"SELECT pg_advisory_unlock({MIGRATION_LOCK_ID})"))
            connection.commit()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
