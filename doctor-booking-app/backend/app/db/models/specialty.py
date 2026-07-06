from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import UUIDPk


class Specialty(UUIDPk, Base):
    __tablename__ = "specialties"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    doctors: Mapped[list["DoctorProfile"]] = relationship(back_populates="specialty")  # noqa: F821
