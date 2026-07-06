import hashlib
import json
import secrets
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.auth.base import ItsmeIdentity, TokenSet
from app.config import Settings
from app.db.models import OAuthTransaction


class MockItsmeProvider:
    """Fake itsme identity provider for local dev/demo — no external network calls.

    Mimics the *shape* of the real OIDC flow closely enough that the callback
    handler (app/api/v1/auth.py) doesn't need to know which provider is active:
    it redirects to a local "consent" HTML page instead of itsme's real login
    screen, then bounces back to the same /auth/itsme/callback with a
    fabricated `code`. Selected automatically when ITSME_* env vars are unset
    (see app/auth/provider.py).
    """

    def __init__(self, settings: Settings, db: Session):
        self.settings = settings
        self.db = db

    async def build_authorization_url(self, state: str, code_challenge: str, nonce: str) -> str:
        params = {"state": state}
        return f"{self.settings.backend_base_url}/api/v1/auth/mock-itsme/consent?{urlencode(params)}"

    def submit_consent(self, state: str, given_name: str, family_name: str, fake_national_number: str) -> str:
        """Called by the mock consent form POST handler. Returns a fabricated code."""
        txn = self.db.get(OAuthTransaction, state)
        if txn is None:
            raise ValueError("unknown or expired login attempt")

        stable_sub = "mock-" + hashlib.sha256(
            f"{given_name}|{family_name}|{fake_national_number}".encode("utf-8")
        ).hexdigest()[:32]

        identity = {
            "sub": stable_sub,
            "given_name": given_name,
            "family_name": family_name,
        }
        code = secrets.token_urlsafe(24)
        txn.mock_code = code
        txn.mock_identity_json = json.dumps(identity)
        self.db.add(txn)
        self.db.commit()
        return code

    async def exchange_code(self, code: str, code_verifier: str, expected_nonce: str) -> TokenSet:
        # The mock has no real token endpoint: the "code" already carries
        # everything we need via the OAuthTransaction row it was stashed in.
        return TokenSet(access_token="mock-access-token", id_token=code)

    async def get_identity(self, token_set: TokenSet, expected_nonce: str) -> ItsmeIdentity:
        txn = (
            self.db.query(OAuthTransaction)
            .filter(OAuthTransaction.mock_code == token_set.id_token)
            .first()
        )
        if txn is None or txn.mock_identity_json is None:
            raise ValueError("mock itsme login was not completed")

        identity = json.loads(txn.mock_identity_json)
        return ItsmeIdentity(
            sub=identity["sub"],
            given_name=identity["given_name"],
            family_name=identity["family_name"],
            date_of_birth=None,
        )
