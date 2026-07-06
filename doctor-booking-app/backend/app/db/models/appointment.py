import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import Timestamped, UUIDPk


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    cancelled_by_patient = "cancelled_by_patient"
    cancelled_by_doctor = "cancelled_by_doctor"
    completed = "completed"
    no_show = "no_show"


class Appointment(UUIDPk, Timestamped, Base):
    __tablename__ = "appointments"

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"), default=AppointmentStatus.booked, nullable=False
    )
    reason_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # The authoritative no-double-booking guarantee is a Postgres EXCLUDE
    # constraint using tstzrange (added in the initial migration, requires
    # btree_gist), not expressible cleanly as a static SQLAlchemy table arg
    # alongside a partial WHERE clause — see migrations/versions/0001_initial.py.
