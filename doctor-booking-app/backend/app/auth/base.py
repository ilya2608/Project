from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass
class ItsmeIdentity:
    """Normalized identity shape, whether it came from real itsme claims or the mock provider."""

    sub: str
    given_name: str
    family_name: str
    date_of_birth: date | None = None

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}".strip()


@dataclass
class TokenSet:
    access_token: str
    id_token: str


class IdentityProvider(Protocol):
    async def build_authorization_url(self, state: str, code_challenge: str, nonce: str) -> str: ...

    async def exchange_code(self, code: str, code_verifier: str, expected_nonce: str) -> TokenSet: ...

    async def get_identity(self, token_set: TokenSet, expected_nonce: str) -> ItsmeIdentity: ...
