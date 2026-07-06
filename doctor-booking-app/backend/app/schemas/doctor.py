import uuid

from pydantic import BaseModel


class SpecialtyOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class SpecialtyCreate(BaseModel):
    name: str
    slug: str


class DoctorOut(BaseModel):
    id: uuid.UUID
    full_name: str
    bio: str | None
    specialty: SpecialtyOut | None
    slot_duration_minutes: int
    is_accepting_bookings: bool

    model_config = {"from_attributes": True}


class DoctorCreate(BaseModel):
    email: str
    full_name: str
    password: str
    specialty_id: uuid.UUID | None = None
    bio: str | None = None
    slot_duration_minutes: int = 30


class DoctorUpdate(BaseModel):
    full_name: str | None = None
    specialty_id: uuid.UUID | None = None
    bio: str | None = None
    slot_duration_minutes: int | None = None
    is_accepting_bookings: bool | None = None
