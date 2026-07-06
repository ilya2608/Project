"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # create_type=False: each enum below is created exactly once, explicitly,
    # right here — passing the same ENUM object into create_table() column
    # definitions would otherwise try to CREATE TYPE a second time.
    user_role = postgresql.ENUM("patient", "doctor", "admin", name="user_role", create_type=False)
    auth_provider = postgresql.ENUM("itsme", "internal", name="auth_provider", create_type=False)
    exception_kind = postgresql.ENUM("block", "extra", name="exception_kind", create_type=False)
    appointment_status = postgresql.ENUM(
        "booked", "cancelled_by_patient", "cancelled_by_doctor", "completed", "no_show",
        name="appointment_status",
        create_type=False,
    )
    user_role.create(op.get_bind(), checkfirst=True)
    auth_provider.create(op.get_bind(), checkfirst=True)
    exception_kind.create(op.get_bind(), checkfirst=True)
    appointment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("email", sa.String(), nullable=True, unique=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auth_provider", auth_provider, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "specialties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
    )

    op.create_table(
        "patient_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("itsme_sub", sa.String(), nullable=False, unique=True),
        sa.Column("national_register_id_hash", sa.String(), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
    )
    op.create_index("ix_patient_profiles_itsme_sub", "patient_profiles", ["itsme_sub"])

    op.create_table(
        "doctor_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("specialty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specialties.id"), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_accepting_bookings", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "admin_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("password_hash", sa.String(), nullable=False),
    )

    op.create_table(
        "weekly_availability_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
    )
    op.create_index("ix_weekly_availability_rules_doctor_id", "weekly_availability_rules", ["doctor_id"])

    op.create_table(
        "availability_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("is_full_day_block", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("kind", exception_kind, nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
    )
    op.create_index("ix_availability_exceptions_doctor_id", "availability_exceptions", ["doctor_id"])

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", appointment_status, nullable=False, server_default="booked"),
        sa.Column("reason_note", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])

    # Authoritative guarantee: no two BOOKED appointments for the same doctor
    # may have overlapping [start_at, end_at) ranges, enforced by Postgres
    # itself (not just application logic) so concurrent booking requests
    # can't race past the app-level check.
    op.execute(
        """
        ALTER TABLE appointments
        ADD CONSTRAINT no_overlapping_doctor_appointments
        EXCLUDE USING gist (
            doctor_id WITH =,
            tstzrange(start_at, end_at) WITH &&
        )
        WHERE (status = 'booked')
        """
    )

    op.create_table(
        "server_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_server_sessions_user_id", "server_sessions", ["user_id"])

    op.create_table(
        "oauth_transactions",
        sa.Column("state", sa.String(), primary_key=True),
        sa.Column("code_verifier", sa.String(), nullable=False),
        sa.Column("nonce", sa.String(), nullable=False),
        sa.Column("mock_code", sa.String(), nullable=True),
        sa.Column("mock_identity_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oauth_transactions")
    op.drop_table("server_sessions")
    op.drop_constraint("no_overlapping_doctor_appointments", "appointments", type_="exclude")
    op.drop_table("appointments")
    op.drop_table("availability_exceptions")
    op.drop_table("weekly_availability_rules")
    op.drop_table("admin_profiles")
    op.drop_table("doctor_profiles")
    op.drop_table("patient_profiles")
    op.drop_table("specialties")
    op.drop_table("users")

    postgresql.ENUM(name="appointment_status").drop(op.get_bind())
    postgresql.ENUM(name="exception_kind").drop(op.get_bind())
    postgresql.ENUM(name="auth_provider").drop(op.get_bind())
    postgresql.ENUM(name="user_role").drop(op.get_bind())
