import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ServerSession, User

settings = get_settings()


def create_session(db: Session, user: User, response: Response, user_agent: str | None = None) -> ServerSession:
    session = ServerSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days),
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    response.set_cookie(
        key=settings.session_cookie_name,
        value=str(session.id),
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_days * 24 * 3600,
        path="/",
    )
    return session


def get_user_for_session_id(db: Session, session_id: str) -> User | None:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None

    session = db.get(ServerSession, sid)
    if session is None:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        return None
    return db.get(User, session.user_id)


def revoke_session(db: Session, session_id: str, response: Response) -> None:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        sid = None

    if sid is not None:
        session = db.get(ServerSession, sid)
        if session is not None:
            db.delete(session)
            db.commit()

    response.delete_cookie(key=settings.session_cookie_name, path="/")
