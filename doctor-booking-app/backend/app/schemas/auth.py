import uuid

from pydantic import BaseModel, EmailStr

from app.db.models.user import UserRole


class MeResponse(BaseModel):
    id: uuid.UUID
    role: UserRole
    full_name: str
    email: str | None = None


class StaffLoginRequest(BaseModel):
    email: EmailStr
    password: str


class MockConsentRequest(BaseModel):
    state: str
    given_name: str
    family_name: str
    fake_national_number: str
