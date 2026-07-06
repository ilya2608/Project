import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import Timestamped, UUIDPk

if TYPE_CHECKING:
    from app.db.models.specialty import Specialty


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class AuthProvider(str, enum.Enum):
    itsme = "itsme"
    internal = "internal"


class User(UUIDPk, Timestamped, Base):
    __tablename__ = "users"

    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(Enum(AuthProvider, name="auth_provider"), nullable=False)

    patient_profile: Mapped["PatientProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    doctor_profile: Mapped["DoctorProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin_profile: Mapped["AdminProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    itsme_sub: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    national_register_id_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped[User] = relationship(back_populates="patient_profile")


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    specialty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specialties.id"), nullable=True
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_accepting_bookings: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="doctor_profile")
    specialty: Mapped["Specialty | None"] = relationship(back_populates="doctors")


class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped[User] = relationship(back_populates="admin_profile")
