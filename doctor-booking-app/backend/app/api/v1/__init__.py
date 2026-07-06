from fastapi import APIRouter

from app.api.v1 import admin, appointments, auth, availability, doctors

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(doctors.router)
api_router.include_router(availability.router)
api_router.include_router(appointments.router)
api_router.include_router(admin.router)
