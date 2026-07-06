"""Exercises RealItsmeProvider (the actual itsme code path, not the mock)
against a throwaway OIDC test double built with respx — discovery, token
exchange, and id_token/nonce validation all run for real, just against a
fake HTTP backend instead of itsme's real servers."""

import time

import pytest
import respx
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt
from httpx import Response

from app.auth.base import TokenSet
from app.auth.itsme_real import RealItsmeProvider
from app.config import Settings

ISSUER = "https://fake-itsme.example.com"
CLIENT_ID = "test-client-id"


@pytest.fixture()
def rsa_key():
    return JsonWebKey.generate_key("RSA", 2048, is_private=True)


@pytest.fixture()
def settings(rsa_key):
    return Settings(
        itsme_issuer=ISSUER,
        itsme_client_id=CLIENT_ID,
        itsme_client_secret="test-secret",
        itsme_redirect_uri="http://localhost:8000/api/v1/auth/itsme/callback",
    )


def _discovery_doc():
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/oauth/authorize",
        "token_endpoint": f"{ISSUER}/oauth/token",
        "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
        "userinfo_endpoint": f"{ISSUER}/oauth/userinfo",
    }


def _sign_id_token(rsa_key, *, nonce="expected-nonce", aud=CLIENT_ID, iss=ISSUER, exp_delta=3600):
    header = {"alg": "RS256", "kid": rsa_key.as_dict()["kid"] if "kid" in rsa_key.as_dict() else "test-key"}
    now = int(time.time())
    claims = {
        "iss": iss,
        "aud": aud,
        "sub": "itsme-subject-123",
        "nonce": nonce,
        "given_name": "Jean",
        "family_name": "Dupont",
        "birthdate": "1985-07-03",
        "iat": now,
        "exp": now + exp_delta,
    }
    return jose_jwt.encode(header, claims, rsa_key).decode("ascii")


@pytest.mark.asyncio
async def test_build_authorization_url_includes_pkce_and_state(settings):
    with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{ISSUER}/.well-known/openid-configuration").mock(
            return_value=Response(200, json=_discovery_doc())
        )
        provider = RealItsmeProvider(settings)
        url = await provider.build_authorization_url(state="abc", code_challenge="chal", nonce="nonce123")

    assert url.startswith(f"{ISSUER}/oauth/authorize?")
    assert "code_challenge=chal" in url
    assert "code_challenge_method=S256" in url
    assert "state=abc" in url
    assert f"client_id={CLIENT_ID}" in url


@pytest.mark.asyncio
async def test_full_exchange_and_identity_validation(settings, rsa_key):
    id_token = _sign_id_token(rsa_key)
    jwks = {"keys": [rsa_key.as_dict(is_private=False)]}

    with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{ISSUER}/.well-known/openid-configuration").mock(
            return_value=Response(200, json=_discovery_doc())
        )
        mock.get(f"{ISSUER}/.well-known/jwks.json").mock(return_value=Response(200, json=jwks))
        mock.post(f"{ISSUER}/oauth/token").mock(
            return_value=Response(200, json={"access_token": "at-123", "id_token": id_token})
        )

        provider = RealItsmeProvider(settings)
        token_set = await provider.exchange_code(code="fake-code", code_verifier="verifier", expected_nonce="expected-nonce")
        identity = await provider.get_identity(token_set, expected_nonce="expected-nonce")

    assert identity.sub == "itsme-subject-123"
    assert identity.given_name == "Jean"
    assert identity.family_name == "Dupont"
    assert identity.full_name == "Jean Dupont"


@pytest.mark.asyncio
async def test_identity_rejected_when_nonce_does_not_match(settings, rsa_key):
    id_token = _sign_id_token(rsa_key, nonce="attacker-supplied-nonce")
    jwks = {"keys": [rsa_key.as_dict(is_private=False)]}

    with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{ISSUER}/.well-known/openid-configuration").mock(
            return_value=Response(200, json=_discovery_doc())
        )
        mock.get(f"{ISSUER}/.well-known/jwks.json").mock(return_value=Response(200, json=jwks))

        provider = RealItsmeProvider(settings)
        token_set = TokenSet(access_token="at", id_token=id_token)

        with pytest.raises(ValueError, match="nonce"):
            await provider.get_identity(token_set, expected_nonce="expected-nonce")


@pytest.mark.asyncio
async def test_identity_rejected_for_wrong_audience(settings, rsa_key):
    id_token = _sign_id_token(rsa_key, aud="someone-elses-client-id")
    jwks = {"keys": [rsa_key.as_dict(is_private=False)]}

    with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{ISSUER}/.well-known/openid-configuration").mock(
            return_value=Response(200, json=_discovery_doc())
        )
        mock.get(f"{ISSUER}/.well-known/jwks.json").mock(return_value=Response(200, json=jwks))

        provider = RealItsmeProvider(settings)
        token_set = TokenSet(access_token="at", id_token=id_token)

        with pytest.raises(Exception):
            await provider.get_identity(token_set, expected_nonce="expected-nonce")
