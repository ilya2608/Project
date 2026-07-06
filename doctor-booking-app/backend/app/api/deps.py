import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.session_store import get_user_for_session_id
from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import User, UserRole


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_user_for_session_id(db, session_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    return user


def require_role(*roles: UserRole) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this action")
        return user

    return dependency


def require_self_or_admin(doctor_id: uuid.UUID, user: User = Depends(get_current_user)) -> User:
    if user.role == UserRole.admin:
        return user
    if user.role == UserRole.doctor and user.id == doctor_id:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this doctor's data")
