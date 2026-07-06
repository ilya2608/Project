import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models.appointment import AppointmentStatus


class AppointmentOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    reason_note: str | None

    model_config = {"from_attributes": True}


class AppointmentCreate(BaseModel):
    doctor_id: uuid.UUID
    start_at: datetime
    reason_note: str | None = None


class AppointmentReschedule(BaseModel):
    new_start_at: datetime
