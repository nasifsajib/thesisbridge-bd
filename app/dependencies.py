"""
app/dependencies.py
-------------------
Reusable FastAPI dependencies.

A "dependency" is a function FastAPI calls automatically before your route,
so the route does not need to repeat boring work such as:

  - reading the "Authorization: Bearer <token>" header,
  - asking Supabase whether the token is valid,
  - returning HTTP 401 when it is not.

Supabase Auth signs the token, and `auth.get_user(token)` verifies it with
Supabase. That means we do not have to write our own JWT secret management.
"""

from fastapi import Header, HTTPException, status

from app.config import ConfigurationError
from app.database import get_auth_client


def _extract_token(authorization: str | None) -> str | None:
    """
    Pull the token out of a header that looks like:

        Authorization: Bearer eyJhbGciOi...

    Returns None when the header is missing or has the wrong shape.
    """
    if not authorization:
        return None

    parts = authorization.split(" ", 1)

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1].strip()
    return token or None


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """
    FastAPI dependency for routes that REQUIRE a logged-in user.

    Usage inside a router:

        @router.get("/me/state")
        def read_state(user: dict = Depends(get_current_user)):
            ...

    Returns a small dictionary: {"id": "...", "email": "...", "token": "..."}.
    """
    token = _extract_token(authorization)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Supabase checks the signature and expiry, then returns the user.
        response = get_auth_client().auth.get_user(token)
        supabase_user = response.user
    except ConfigurationError:
        # The .env file is missing: let main.py answer with a clear HTTP 503.
        raise
    except Exception:
        # Bad signature, expired token, deleted account, network problem...
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if supabase_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": supabase_user.id,
        "email": supabase_user.email,
        "token": token,
    }


def get_optional_user(authorization: str | None = Header(default=None)) -> dict | None:
    """
    FastAPI dependency for public routes that ALSO want to know the user when
    one is logged in.

    Example: sending a connection request works for guests and members, but
    when a member sends it we attach their user id.

    A broken token is treated as "guest" instead of an error, because the
    route itself is public.
    """
    token = _extract_token(authorization)

    if token is None:
        return None

    try:
        response = get_auth_client().auth.get_user(token)
        supabase_user = response.user
    except Exception:
        return None

    if supabase_user is None:
        return None

    return {
        "id": supabase_user.id,
        "email": supabase_user.email,
        "token": token,
    }
