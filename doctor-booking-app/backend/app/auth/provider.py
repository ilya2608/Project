from sqlalchemy.orm import Session

from app.auth.base import IdentityProvider
from app.auth.itsme_mock import MockItsmeProvider
from app.auth.itsme_real import RealItsmeProvider
from app.config import Settings


def get_identity_provider(settings: Settings, db: Session) -> IdentityProvider:
    """The entire real-vs-mock toggle: presence of itsme env vars.

    Callers (app/api/v1/auth.py) only ever talk to the IdentityProvider
    protocol, so switching from mock to real itsme in production is purely a
    matter of setting ITSME_ISSUER/ITSME_CLIENT_ID/ITSME_CLIENT_SECRET — no
    code change required.
    """
    if settings.itsme_configured:
        return RealItsmeProvider(settings)
    return MockItsmeProvider(settings, db)
