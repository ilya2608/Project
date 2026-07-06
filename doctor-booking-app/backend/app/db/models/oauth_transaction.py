from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OAuthTransaction(Base):
    """Short-lived server-side record of an in-flight itsme login attempt.

    Keyed by `state` so the callback can recover the PKCE code_verifier and
    nonce it needs to validate the response. Also doubles as the mock
    provider's code->fabricated-identity lookup (see app/auth/itsme_mock.py).
    """

    __tablename__ = "oauth_transactions"

    state: Mapped[str] = mapped_column(String, primary_key=True)
    code_verifier: Mapped[str] = mapped_column(String, nullable=False)
    nonce: Mapped[str] = mapped_column(String, nullable=False)
    mock_code: Mapped[str | None] = mapped_column(String, nullable=True)
    mock_identity_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
