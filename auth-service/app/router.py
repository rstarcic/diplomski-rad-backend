import logging
import os
from urllib.parse import urlencode

import aiohttp
from app.dependecies import get_current_user
from app.models import User
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    authenticate_user,
    create_session,
    refresh_session,
    register_user,
    revoke_session,
)
from app.services.google_service import (
    create_google_user,
    exchange_code_for_tokens,
    get_or_raise_google_user,
    verify_google_token,
)
from app.services.password_reset_service import request_password_reset, reset_password
from app.services.pkce_service import consume_pkce_session, create_pkce_session
from app.utils.cookies import attach_auth_cookies
from app.utils.email import send_password_reset_email
from database import get_db
from errors import get_error_code, raise_auth_error
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

CLIENT_ENDPOINT = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://localhost:8001").rstrip("/")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_ENDPOINT = os.getenv(
    "GOOGLE_AUTH_ENDPOINT", "https://accounts.google.com/o/oauth2/v2/auth"
)


async def _init_core_profile(user: User) -> None:
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.post(
                f"{CORE_SERVICE_URL}/profiles/init",
                json={
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                    "profile_picture": user.profile_picture,
                },
                headers={"x-internal-secret": INTERNAL_SECRET},
            ) as response:
                if response.status not in (200, 201):
                    logger.error(
                        "Core profile init failed with status %s for user %s",
                        response.status,
                        user.id,
                    )
    except Exception as exc:
        logger.error("Failed to create core profile for user %s: %s", user.id, exc)


@router.post("/register/client", response_model=RegisterResponse)
async def register_client(data: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, data, "client")
    await _init_core_profile(user)
    return user


@router.post("/register/contractor", response_model=RegisterResponse)
async def register_contractor(data: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, data, "contractor")
    await _init_core_profile(user)
    return user


@router.post("/login", response_model=LoginResponse)
def login_user(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user, access_token, refresh_token = authenticate_user(db, data)
    attach_auth_cookies(response, access_token, refresh_token)
    return {"message": "Authenticated", "user": user}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("app_refresh")
    if refresh_token:
        revoke_session(db, refresh_token)
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("app_access")
    response.delete_cookie("app_refresh")
    return response


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    old_refresh = request.cookies.get("app_refresh")
    if not old_refresh:
        raise_auth_error("not_authenticated")
    access_token, refresh_token = refresh_session(db, old_refresh)
    attach_auth_cookies(response, access_token, refresh_token)
    return {"message": "Refreshed"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    result = request_password_reset(db, data.email)
    if result:
        raw_token, full_name = result
        try:
            send_password_reset_email(data.email, raw_token, full_name)
        except Exception as exc:
            logger.error(
                "Failed to send password reset email to %s: %s", data.email, exc
            )
            raise_auth_error("email_send_failed")
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password_endpoint(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_password(db, data.token, data.new_password)
    return {"message": "Password reset successfully."}


@router.get("/google/login/start")
def google_login_start(db: Session = Depends(get_db)):
    state, challenge = create_pkce_session(db, "login")
    return RedirectResponse(url=_build_google_url(state, challenge))


@router.get("/google/register/start")
def google_register_start(role: str, db: Session = Depends(get_db)):
    if role not in ["client", "contractor"]:
        raise_auth_error("invalid_role")
    state, challenge = create_pkce_session(db, role)
    return RedirectResponse(url=_build_google_url(state, challenge))


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if request.query_params.get("error"):
            return RedirectResponse(
                f"{CLIENT_ENDPOINT}/error?error=google_oauth_cancelled"
            )
        if not code or not state:
            raise_auth_error("missing_code_or_state")

        code_verifier, flow_type = consume_pkce_session(db, state)
        token_data = await exchange_code_for_tokens(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code_verifier": code_verifier,
            }
        )

        claims = verify_google_token(token_data.get("id_token"))
        if flow_type == "login":
            user = get_or_raise_google_user(db, claims)
        else:
            user = create_google_user(db, claims, flow_type)
            await _init_core_profile(user)

        response = RedirectResponse(
            url=f"{CLIENT_ENDPOINT}/{user.role}/dashboard", status_code=302
        )
        access_token, refresh_token = create_session(db, user)
        attach_auth_cookies(response, access_token, refresh_token)
        return response

    except HTTPException as e:
        return RedirectResponse(
            f"{CLIENT_ENDPOINT}/error?error={get_error_code(e.detail)}"
        )


def _build_google_url(state: str, challenge: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"
