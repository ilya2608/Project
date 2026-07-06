# itsme integration notes

This app authenticates patients using **itsme**, the Belgian digital identity
app, via standard OpenID Connect (authorization code + PKCE).

## Local development / demo (default)

By default `ITSME_ISSUER`, `ITSME_CLIENT_ID`, and `ITSME_CLIENT_SECRET` are
unset. When any of them is missing, the backend automatically uses a **mock
itsme provider** (`backend/app/auth/itsme_mock.py`) instead of the real
service:

- `GET /api/v1/auth/itsme/login` redirects to a local fake "itsme" consent
  page instead of the real itsme login screen.
- You type in a name (and a placeholder national number) instead of
  authenticating with the itsme app on your phone.
- The rest of the flow — callback, session creation, redirect into the app —
  is identical code to what runs with real itsme; only the identity-provider
  implementation differs (see `backend/app/auth/base.py` /
  `backend/app/auth/provider.py`).
- The same fake name+number always maps to the same account, so you can
  "log back in" as the same test patient repeatedly.

This means the entire app — booking, cancelling, doctor agendas, admin views
— is fully usable and demoable with zero external dependencies.

## Getting real itsme credentials

itsme is only available as a **registered partner/merchant integration** —
there is no self-service API key signup. To go live you (the clinic/business
running this app) need to:

1. Register as an itsme partner (directly with itsme, or via one of the
   Belgian bank/telco brokers that resell itsme integration), and complete
   their onboarding/compliance process.
2. Obtain a `client_id` / `client_secret` and register your redirect URI(s)
   with them.
3. Get the OIDC issuer URL for the environment you're targeting (itsme
   provides separate sandbox/acceptance and production environments).

None of this can be done from inside this codebase — it's a business/legal
step with itsme, not a technical one.

## Switching to real itsme

Once you have those three values, set them in `.env` (or your production
secrets store):

```
ITSME_ISSUER=https://<itsme-issuer-for-your-environment>
ITSME_CLIENT_ID=<your client id>
ITSME_CLIENT_SECRET=<your client secret>
ITSME_REDIRECT_URI=https://your-domain.example/api/v1/auth/itsme/callback
```

Restart the backend. `app/auth/provider.py` will now return
`RealItsmeProvider` instead of the mock, and `/auth/itsme/login` will redirect
to the real itsme authorization endpoint. No other code changes are required.

Before going live, confirm with itsme's partner documentation:
- the exact `scope` values available to you (this app requests `openid
  profile` by default — see `ITSME_SCOPES` in `.env`),
- which claims (name, birthdate, national register number, etc.) your itsme
  contract entitles you to receive, and adjust
  `backend/app/auth/itsme_real.py`'s claim extraction accordingly,
- itsme's exact redirect URI and HTTPS requirements for production.
