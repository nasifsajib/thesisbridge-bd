"""
app/database.py
---------------
Creates and reuses the two Supabase clients the backend needs.

WHY TWO CLIENTS?

1. `get_auth_client()` uses the ANON key.
   Supabase Auth endpoints (sign up, sign in, verify a token) are designed to
   be called with the anon key. Using the service role key for those calls
   would give the account more power than it should have.

2. `get_admin_client()` uses the SERVICE ROLE key.
   Table queries and profile inserts need permission to bypass Row Level
   Security, so they use the service role key. This key stays on the server.

Creating a new client on every request would be slow, so each client is
created once and then reused (a simple lazy singleton).
"""

from supabase import Client, create_client

from app.config import (
    SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    ensure_settings,
)

# Module-level variables that hold the clients after the first use.
_auth_client: Client | None = None
_admin_client: Client | None = None


def get_auth_client() -> Client:
    """
    Return the client used for Supabase Auth operations.

    It uses the public anon key, which is the normal key for auth calls.
    """
    global _auth_client

    if _auth_client is None:
        ensure_settings()
        _auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    return _auth_client


def get_admin_client() -> Client:
    """
    Return the client used to read and write database tables.

    It uses the service role key, so it can bypass Row Level Security.
    Never expose this client (or its key) to the frontend.
    """
    global _admin_client

    if _admin_client is None:
        ensure_settings()
        _admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    return _admin_client
