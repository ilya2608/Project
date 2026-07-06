import enum
import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import UUIDPk


class ExceptionKind(str, enum.Enum):
    block = "block"
    extra = "extra"


class WeeklyAvailabilityRule(UUIDPk, Base):
    __tablename__ = "weekly_availability_rules"

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)


class AvailabilityException(UUIDPk, Base):
    __tablename__ = "availability_exceptions"

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_full_day_block: Mapped[bool] = mapped_column(Boolean, default=False)
    kind: Mapped[ExceptionKind] = mapped_column(Enum(ExceptionKind, name="exception_kind"), nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
