"""
app/config.py
-------------
All environment settings (secrets and URLs) are read here, in ONE place.

Locally the values come from a file named `.env` in the project root.
On Vercel the values come from the project's Environment Variables settings.
Both cases work without changing any code, because we always read
`os.environ`.
"""

import os

from dotenv import load_dotenv

# load_dotenv() reads a local `.env` file if one exists.
# On Vercel there is no `.env` file, so this line simply does nothing there.
load_dotenv()

# ---------------------------------------------------------------------------
# Supabase settings
# ---------------------------------------------------------------------------
# SUPABASE_URL                -> https://<project-ref>.supabase.co
# SUPABASE_ANON_KEY           -> public key, used only for Supabase Auth calls
# SUPABASE_SERVICE_ROLE_KEY   -> secret key, used for database queries.
#                                It bypasses Row Level Security, so it must
#                                NEVER be sent to the browser.
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# ---------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------------------------------
# During local development the HTML is served from port 8417 while the API
# runs on port 8000. Browsers block that cross-origin request unless the API
# sends CORS headers, so we allow the origins listed here.
#
# Default "*" means "any origin" and is fine for this student project because
# we authenticate with a Bearer token (not cookies). In production you can
# restrict it, for example:
#   CORS_ORIGINS=https://thesisbridge-bd.vercel.app
# ---------------------------------------------------------------------------
_raw_cors_origins = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [
    origin.strip() for origin in _raw_cors_origins.split(",") if origin.strip()
]


class ConfigurationError(RuntimeError):
    """
    Raised when required environment variables are missing.

    main.py turns this into a clean HTTP 503 answer instead of a traceback.
    """


def missing_settings() -> list[str]:
    """
    Return the names of environment variables that are still empty.

    The function is used by /api/health (to report a setup problem politely)
    and by database.py (to stop with a clear error message instead of a
    confusing Supabase stack trace).
    """
    missing = []

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_ANON_KEY:
        missing.append("SUPABASE_ANON_KEY")
    if not SUPABASE_SERVICE_ROLE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    return missing


def ensure_settings() -> None:
    """
    Raise a RuntimeError that a human can understand if keys are missing.

    Called before the first Supabase client is created.
    """
    missing = missing_settings()

    if missing:
        raise ConfigurationError(
            "Missing environment variables: "
            + ", ".join(missing)
            + ". Copy `.env.example` to `.env` and fill in your Supabase keys, "
            "or add them in the Vercel project settings."
        )
