# Doctor Booking

A web-based appointment booking system for a multi-doctor clinic. Patients log
in with **itsme** and book appointments with a doctor; doctors manage their
own availability and agenda; admin/staff manage the roster of doctors and can
see appointments across the whole clinic.

No native app — this is a website, works in any modern browser (including on
mobile).

## Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic, Postgres.
- **Frontend**: React + TypeScript (Vite), MUI.
- **Auth**: itsme OIDC (authorization code + PKCE) for patients; email +
  password for doctors/admin. A built-in **mock itsme** identity provider
  lets you run and demo the whole app locally without real itsme credentials
  — see [`ITSME.md`](./ITSME.md).

## Quickstart (local dev)

```bash
cp .env.example .env
docker compose up --build
```

Once the containers are up, seed some demo data (specialties, doctors with
availability, an admin account):

```bash
docker compose exec backend python -m scripts.seed_dev_data
```

Then open http://localhost:5173:

- **Patient**: click "Log in with itsme" — since `ITSME_*` env vars are blank
  by default, you'll land on a mock itsme consent screen. Pick any name and
  you're logged in as that (fake) patient.
- **Doctor**: go to "Doctor/staff login" and use one of the seeded accounts
  printed by the seed script (e.g. `dr.peeters@example.com`).
- **Admin**: same staff login screen, `admin@example.com`.

## Running tests

```bash
docker compose exec backend pytest
```

## Going live with real itsme

Once you have real itsme partner/merchant credentials, set `ITSME_ISSUER`,
`ITSME_CLIENT_ID`, `ITSME_CLIENT_SECRET`, and `ITSME_REDIRECT_URI` in `.env`
and restart the backend. The app automatically switches from the mock
identity provider to the real itsme OIDC flow — no code changes needed. See
[`ITSME.md`](./ITSME.md) for details.
