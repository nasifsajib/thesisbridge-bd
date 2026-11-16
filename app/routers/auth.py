"""
app/routers/auth.py
-------------------
Account endpoints. Supabase Auth owns the password hashing and the tokens;
this file only coordinates the steps.

    POST /api/auth/signup   create an auth user + a profile row, return a token
    POST /api/auth/login    verify email + password, return a token
    GET  /api/auth/me       return the logged-in user's profile

WHY THE ADMIN API FOR SIGN-UP?
A normal Supabase sign-up sends a confirmation email. A student project may
not have an email sender configured, and then the account can never log in.
Creating the user with `auth.admin.create_user(email_confirm=True)` marks the
address as confirmed immediately, so the demo always works. Passwords are
still hashed and checked by Supabase Auth - we never see or store them.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import ConfigurationError
from app.database import get_admin_client, get_auth_client
from app.dependencies import get_current_user
from app.schemas import AuthResponse, LoginRequest, SignupRequest, UserOut

router = APIRouter()


# ===========================================================================
# Helpers
# ===========================================================================


def _clean(value: str | None) -> str | None:
    """
    Turn empty form fields into NULL.

    The browser sends "" for an optional field that was left blank. Storing
    NULL instead of "" keeps the database tidy.
    """
    if value is None:
        return None

    value = value.strip()
    return value or None


def _profile_for(user_id: str) -> dict | None:
    """Read one profile row, or return None when it does not exist yet."""
    db = get_admin_client()
    response = (
        db.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _ensure_profile(
    user_id: str,
    email: str | None,
    metadata: dict | None = None,
) -> dict:
    """
    Return the profile for an auth user, creating a minimal one if needed.

    This covers accounts that were created directly in the Supabase dashboard
    (those have no profile row yet).
    """
    profile = _profile_for(user_id)

    if profile is not None:
        return profile

    db = get_admin_client()
    safe_email = email or ""
    safe_metadata = metadata or {}
    name = safe_metadata.get("name") or safe_email.split("@")[0] or "Student"

    row = {
        "id": user_id,
        "name": name,
        "email": safe_email,
        "university": None,
        "department": None,
        "student_id": None,
        "interest": None,
    }
    db.table("profiles").insert(row).execute()

    created = _profile_for(user_id)

    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The account exists but its profile could not be created.",
        )

    return created


def _token_from_session(result) -> str:
    """Read the access token out of a Supabase auth response."""
    session = getattr(result, "session", None)

    if session is None or not getattr(session, "access_token", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account still needs email confirmation. "
            "Confirm the address, then log in again.",
        )

    return session.access_token


# ===========================================================================
# POST /api/auth/signup
# ===========================================================================


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def signup(payload: SignupRequest) -> AuthResponse:
    admin = get_admin_client()
    email = payload.email.lower()

    # ---- Step 1: create the authentication record ------------------------
    try:
        created = admin.auth.admin.create_user(
            {
                "email": email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {"name": payload.name},
            }
        )
    except Exception as exc:
        message = str(exc).lower()

        if "already" in message or "exists" in message or "registered" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please log in.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create the account. Please check the email and "
            "password, then try again.",
        )

    auth_user = getattr(created, "user", None)

    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase did not return the new user.",
        )

    # ---- Step 2: create the public profile row ---------------------------
    profile_row = {
        "id": auth_user.id,
        "name": payload.name.strip(),
        "email": email,
        "university": _clean(payload.university),
        "department": _clean(payload.department),
        "student_id": _clean(payload.student_id),
        "interest": _clean(payload.interest),
    }

    try:
        admin.table("profiles").insert(profile_row).execute()
    except Exception:
        # Roll back step 1 so we never leave an auth user with no profile.
        try:
            admin.auth.admin.delete_user(auth_user.id)
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The profile could not be saved, so the account was not created.",
        )

    # ---- Step 3: log the new user in ------------------------------------
    try:
        session_result = get_auth_client().auth.sign_in_with_password(
            {"email": email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account created, but automatic login failed. Please log in.",
        )

    profile = _profile_for(auth_user.id) or profile_row

    return AuthResponse(
        access_token=_token_from_session(session_result),
        user=UserOut.model_validate(profile),
    )


# ===========================================================================
# POST /api/auth/login
# ===========================================================================


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Log in with email and password",
)
def login(payload: LoginRequest) -> AuthResponse:
    try:
        result = get_auth_client().auth.sign_in_with_password(
            {"email": payload.email.lower(), "password": payload.password}
        )
    except ConfigurationError:
        # Missing .env values are a server setup problem, not a wrong password.
        raise
    except Exception:
        # We deliberately do not say whether the email or the password was
        # wrong: that would let an attacker discover registered addresses.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    auth_user = getattr(result, "user", None)

    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    profile = _ensure_profile(
        auth_user.id,
        auth_user.email,
        auth_user.user_metadata,
    )

    return AuthResponse(
        access_token=_token_from_session(result),
        user=UserOut.model_validate(profile),
    )


# ===========================================================================
# GET /api/auth/me
# ===========================================================================


@router.get(
    "/me",
    response_model=UserOut,
    summary="The logged-in user's profile",
)
def me(current_user: dict = Depends(get_current_user)) -> UserOut:
    profile = _profile_for(current_user["id"])

    if profile is None:
        # The token is valid but the profile row is missing; repair it.
        profile = _ensure_profile(current_user["id"], current_user["email"])

    return UserOut.model_validate(profile)
