import uuid
from datetime import date, datetime, time

from pydantic import BaseModel

from app.db.models.availability import ExceptionKind


class WeeklyRuleOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    weekday: int
    start_time: time
    end_time: time
    valid_from: date | None
    valid_until: date | None

    model_config = {"from_attributes": True}


class WeeklyRuleCreate(BaseModel):
    weekday: int
    start_time: time
    end_time: time
    valid_from: date | None = None
    valid_until: date | None = None


class ExceptionOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    date: date
    start_time: time | None
    end_time: time | None
    is_full_day_block: bool
    kind: ExceptionKind
    reason: str | None

    model_config = {"from_attributes": True}


class ExceptionCreate(BaseModel):
    date: date
    start_time: time | None = None
    end_time: time | None = None
    is_full_day_block: bool = False
    kind: ExceptionKind
    reason: str | None = None


class SlotOut(BaseModel):
    start_at: datetime
    end_at: datetime


class SlotsByDate(BaseModel):
    date: date
    slots: list[SlotOut]
