"""
app/main.py
-----------
The entry point of the backend.

FastAPI reads the routers registered below and builds:

  - the real endpoints under /api/...
  - interactive documentation at /docs (great for a demo: you can click
    "Try it out" on every endpoint)

Vercel looks for an object named `app` in this file, so the name matters.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError

from app.config import CORS_ORIGINS, ConfigurationError, missing_settings
from app.routers import auth, content, requests, user_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("thesisbridge")


# ===========================================================================
# 1. Create the application
# ===========================================================================

app = FastAPI(
    title="ThesisBridge BD API",
    version="1.0.0",
    description=(
        "Python backend for ThesisBridge BD. "
        "Content is stored in Supabase PostgreSQL; accounts use Supabase Auth. "
        "Open /docs to try every endpoint."
    ),
)


# ===========================================================================
# 2. CORS
# ===========================================================================
# A browser refuses to call http://127.0.0.1:8000 from http://127.0.0.1:8417
# unless the API says it is allowed. CORSMiddleware adds those headers.
#
# allow_credentials=False is correct here because the frontend sends a
# Bearer token, not cookies. (Browsers also forbid "*" + credentials.)
# ===========================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# 3. Routers
# ===========================================================================
# Every route lives under /api so it never collides with the HTML pages that
# Vercel serves from the public/ folder.
# ===========================================================================

app.include_router(content.router, prefix="/api", tags=["Public content"])
app.include_router(auth.router, prefix="/api/auth", tags=["Accounts"])
app.include_router(user_state.router, prefix="/api/me", tags=["My data"])
app.include_router(requests.router, prefix="/api", tags=["Connection requests"])


# ===========================================================================
# 4. Health check
# ===========================================================================


@app.get("/api/health", tags=["Health"], summary="Is the API configured?")
def health() -> dict:
    """
    Returns 200 even when the database keys are missing, so you can open this
    URL first when something is wrong.

    `databaseConfigured: false` means the .env file (or the Vercel
    environment variables) still needs the three Supabase values.
    """
    missing = missing_settings()

    return {
        "status": "ok",
        "service": "ThesisBridge BD API",
        "version": "1.0.0",
        "databaseConfigured": len(missing) == 0,
        "missingSettings": missing,
    }


# ===========================================================================
# 5. Friendly error when Supabase is not configured yet
# ===========================================================================


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(
    request: Request,
    exc: ConfigurationError,
) -> JSONResponse:
    """
    Instead of a long Python traceback, the browser receives a readable
    message: "Missing environment variables: ...".
    """
    logger.error("Configuration error: %s", exc)

    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


# ===========================================================================
# 5b. Friendly error when a database query fails
# ===========================================================================
# Supabase answers through PostgREST. When a query is wrong (or the tables have
# not been created yet) the supabase-py library raises APIError, and without a
# handler here FastAPI would return a bare "Internal Server Error" that tells
# nobody anything useful.
#
# This handler turns that into 503 + a sentence that says what to do next.
# It is also what the website shows in its warning toast, because api.js reads
# the "detail" field of every error response.
# ===========================================================================


@app.exception_handler(APIError)
async def database_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    """
    Translate a PostgREST error into a readable HTTP response.

    The most common one on a fresh project is PGRST205: the table does not
    exist yet, because sql/001_create_tables.sql has not been run.
    """
    # APIError stores the fields PostgREST sent as attributes: .code, .message,
    # .hint and .details. (Reading them directly is clearer than parsing text.)
    code = exc.code or ""
    message = exc.message or "Unknown database error."

    if code == "PGRST205":
        detail = (
            "The database tables do not exist yet. Open the Supabase dashboard, "
            "go to SQL Editor, and run the file sql/001_create_tables.sql "
            "(one paste, then press Run)."
        )
    elif code == "42501":
        detail = (
            "The database refused this query for permission reasons. Check that "
            "SUPABASE_SERVICE_ROLE_KEY holds the secret key, not the publishable one."
        )
    else:
        detail = f"Database error ({code or 'unknown'}): {message}"

    logger.error("Database error [%s]: %s", code, message)

    return JSONResponse(
        status_code=503,
        content={"detail": detail},
    )


# ===========================================================================
# 6. A tiny root route for local development
# ===========================================================================
# In production Vercel serves public/index.html at "/", so this route is never
# reached there. Locally it tells you the API is alive.
# ===========================================================================


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "message": "ThesisBridge BD API is running.",
        "documentation": "/docs",
        "health": "/api/health",
        "content": "/api/content",
    }


# ===========================================================================
# 7. Startup log
# ===========================================================================


@app.on_event("startup")
def log_startup_state() -> None:
    missing = missing_settings()

    if missing:
        logger.warning(
            "Supabase is not configured yet. Missing: %s",
            ", ".join(missing),
        )
    else:
        logger.info("Supabase configuration loaded.")
