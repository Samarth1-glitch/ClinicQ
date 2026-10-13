"""add indexes used by the queue and schedule lookups

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-13 11:00:00
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_appointments_scheduled_at", "appointments", ["scheduled_at"])
    op.create_index(
        "ix_appointments_doctor_scheduled", "appointments", ["doctor_id", "scheduled_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_doctor_scheduled", table_name="appointments")
    op.drop_index("ix_appointments_scheduled_at", table_name="appointments")
