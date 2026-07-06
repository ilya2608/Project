from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.models import User


def authenticate_staff(db: Session, email: str, password: str) -> User | None:
    """Verifies email+password for a doctor or admin account."""
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if user is None:
        return None

    password_hash: str | None = None
    if user.doctor_profile is not None:
        password_hash = user.doctor_profile.password_hash
    elif user.admin_profile is not None:
        password_hash = user.admin_profile.password_hash

    if password_hash is None or not verify_password(password, password_hash):
        return None

    return user
