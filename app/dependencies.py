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

from fastapi import Depends, Header, HTTPException, status
from postgrest.exceptions import APIError

from app.config import ConfigurationError
from app.database import get_admin_client, get_auth_client


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


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency for ADMIN-ONLY routes.

    Usage inside a router:

        @router.get("/overview")
        def overview(admin: dict = Depends(require_admin)):
            ...

    How it works:
      1. `get_current_user` already proved the token is valid (else 401).
      2. We read the `is_admin` flag of that user's profile row.
      3. A normal student gets 403 Forbidden - the request is refused by the
         SERVER, not merely hidden by the page. Typing /admin.html by hand
         therefore shows nothing useful: every call behind this dependency
         answers 403.

    The flag is read from the database on every admin request instead of being
    trusted from the token, so revoking admin access takes effect immediately
    and cannot be forged by editing a token on the client.
    """
    db = get_admin_client()

    try:
        rows = (
            db.table("profiles")
            .select("is_admin")
            .eq("id", current_user["id"])
            .limit(1)
            .execute()
            .data
        )
    except APIError as exc:
        # A fresh copy of the project may not have run sql/002_admin.sql yet.
        # Say that in plain words instead of "column profiles.is_admin missing".
        if exc.code == "42703":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "The administrator flag is missing from the database. "
                    "Open the Supabase dashboard, go to SQL Editor, and run "
                    "sql/002_admin.sql once."
                ),
            )
        raise

    if not rows or not rows[0].get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required for this page.",
        )

    return current_user


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
