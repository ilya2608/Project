import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models.appointment import AppointmentStatus


class AdminAppointmentOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    doctor_name: str
    patient_id: uuid.UUID
    patient_name: str
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
