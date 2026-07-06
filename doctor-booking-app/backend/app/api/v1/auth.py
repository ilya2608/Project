from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.auth.internal import authenticate_staff
from app.auth.itsme_mock import MockItsmeProvider
from app.auth.provider import get_identity_provider
from app.auth.session_store import create_session, revoke_session
from app.config import Settings, get_settings
from app.core.security import derive_code_challenge, generate_code_verifier, generate_nonce, generate_state
from app.db.base import get_db
from app.db.models import AuthProvider, OAuthTransaction, PatientProfile, User, UserRole
from app.schemas.auth import MeResponse, StaffLoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/itsme/login")
async def itsme_login(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    state = generate_state()
    nonce = generate_nonce()
    code_verifier = generate_code_verifier()
    code_challenge = derive_code_challenge(code_verifier)

    db.add(OAuthTransaction(state=state, code_verifier=code_verifier, nonce=nonce))
    db.commit()

    provider = get_identity_provider(settings, db)
    url = await provider.build_authorization_url(state=state, code_challenge=code_challenge, nonce=nonce)
    return RedirectResponse(url)


@router.get("/itsme/callback")
async def itsme_callback(
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    txn = db.get(OAuthTransaction, state)
    if txn is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown or expired login attempt")

    provider = get_identity_provider(settings, db)
    token_set = await provider.exchange_code(code=code, code_verifier=txn.code_verifier, expected_nonce=txn.nonce)
    identity = await provider.get_identity(token_set, expected_nonce=txn.nonce)

    db.delete(txn)
    db.commit()

    patient_profile = db.query(PatientProfile).filter(PatientProfile.itsme_sub == identity.sub).first()
    if patient_profile is None:
        user = User(
            role=UserRole.patient,
            full_name=identity.full_name,
            auth_provider=AuthProvider.itsme,
        )
        db.add(user)
        db.flush()
        patient_profile = PatientProfile(
            user_id=user.id,
            itsme_sub=identity.sub,
            date_of_birth=identity.date_of_birth,
        )
        db.add(patient_profile)
        db.commit()
    else:
        user = db.get(User, patient_profile.user_id)

    redirect = RedirectResponse(url=f"{settings.frontend_base_url}/patient/doctors")
    create_session(db, user, redirect)
    return redirect


@router.get("/mock-itsme/consent", response_class=HTMLResponse)
async def mock_itsme_consent_form(state: str, settings: Settings = Depends(get_settings)) -> str:
    if settings.itsme_configured:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock itsme is disabled")

    return f"""
    <html>
      <head><title>MOCK itsme</title></head>
      <body style="font-family: sans-serif; max-width: 420px; margin: 60px auto;">
        <h2>🟠 MOCK itsme — for local development only</h2>
        <p>This stands in for the real itsme login screen. Pick any name to
        "log in" as that (fake) person; the same name+number will always map
        back to the same account.</p>
        <form method="post" action="/api/v1/auth/mock-itsme/consent">
          <input type="hidden" name="state" value="{state}" />
          <label>First name<br/><input name="given_name" value="Jean" required /></label><br/><br/>
          <label>Last name<br/><input name="family_name" value="Dupont" required /></label><br/><br/>
          <label>Fake national number<br/><input name="fake_national_number" value="85073003328" required /></label><br/><br/>
          <button type="submit">Log in as this person</button>
        </form>
      </body>
    </html>
    """


@router.post("/mock-itsme/consent")
async def mock_itsme_consent_submit(
    state: str = Form(...),
    given_name: str = Form(...),
    family_name: str = Form(...),
    fake_national_number: str = Form(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if settings.itsme_configured:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock itsme is disabled")

    provider = MockItsmeProvider(settings, db)
    code = provider.submit_consent(state, given_name, family_name, fake_national_number)
    return RedirectResponse(
        url=f"/api/v1/auth/itsme/callback?code={code}&state={state}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/staff/login")
def staff_login(
    payload: StaffLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> MeResponse:
    user = authenticate_staff(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    create_session(db, user, response)
    return MeResponse(id=user.id, role=user.role, full_name=user.full_name, email=user.email)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    session_id = request.cookies.get(settings.session_cookie_name)
    if session_id:
        revoke_session(db, session_id, response)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(id=user.id, role=user.role, full_name=user.full_name, email=user.email)
