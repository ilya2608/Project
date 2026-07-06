from datetime import date, datetime
from urllib.parse import urlencode

import httpx
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt

from app.auth.base import ItsmeIdentity, TokenSet
from app.config import Settings


class RealItsmeProvider:
    """Standards-compliant OIDC authorization-code + PKCE client for itsme.

    Requires ITSME_ISSUER/ITSME_CLIENT_ID/ITSME_CLIENT_SECRET to be set —
    see app/auth/provider.py for the real-vs-mock toggle. All endpoints are
    discovered from the issuer's well-known document, so this class works
    against any spec-compliant OIDC provider (itsme in production, or a
    throwaway OIDC test double in tests/CI).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._discovery_doc: dict | None = None
        self._jwks: dict | None = None

    async def _discovery(self) -> dict:
        if self._discovery_doc is None:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.settings.itsme_issuer}/.well-known/openid-configuration")
                resp.raise_for_status()
                self._discovery_doc = resp.json()
        return self._discovery_doc

    async def _jwks_keys(self) -> dict:
        if self._jwks is None:
            discovery = await self._discovery()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(discovery["jwks_uri"])
                resp.raise_for_status()
                self._jwks = JsonWebKey.import_key_set(resp.json())
        return self._jwks

    async def build_authorization_url(self, state: str, code_challenge: str, nonce: str) -> str:
        discovery = await self._discovery()
        params = {
            "response_type": "code",
            "client_id": self.settings.itsme_client_id,
            "redirect_uri": self.settings.itsme_redirect_uri,
            "scope": self.settings.itsme_scopes,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{discovery['authorization_endpoint']}?{urlencode(params)}"

    async def exchange_code(self, code: str, code_verifier: str, expected_nonce: str) -> TokenSet:
        discovery = await self._discovery()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                discovery["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.settings.itsme_redirect_uri,
                    "client_id": self.settings.itsme_client_id,
                    "client_secret": self.settings.itsme_client_secret,
                    "code_verifier": code_verifier,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return TokenSet(access_token=data["access_token"], id_token=data["id_token"])

    async def get_identity(self, token_set: TokenSet, expected_nonce: str) -> ItsmeIdentity:
        keys = await self._jwks_keys()
        claims = jose_jwt.decode(
            token_set.id_token,
            keys,
            claims_options={
                "iss": {"essential": True, "value": self.settings.itsme_issuer},
                "aud": {"essential": True, "value": self.settings.itsme_client_id},
            },
        )
        claims.validate(now=int(datetime.utcnow().timestamp()))

        if claims.get("nonce") != expected_nonce:
            raise ValueError("id_token nonce does not match the nonce issued for this login attempt")

        dob_raw = claims.get("birthdate")
        dob = date.fromisoformat(dob_raw) if dob_raw else None

        return ItsmeIdentity(
            sub=claims["sub"],
            given_name=claims.get("given_name", ""),
            family_name=claims.get("family_name", ""),
            date_of_birth=dob,
        )
