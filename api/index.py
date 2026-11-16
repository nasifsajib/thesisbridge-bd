"""
api/index.py
------------
The only file Vercel needs to see.

Vercel's Python runtime treats a file inside the `api/` folder as a serverless
function. Our real application lives in `app/main.py` (a Python package, which
Vercel does not scan for entry points), so this file is a one-line bridge:

    Vercel  ->  api/index.py  ->  app/main.py  ->  the same FastAPI object
                                that `uvicorn app.main:app` runs locally.

Keeping the shim separate means the project runs identically in both places:
locally we start `app.main:app`, on Vercel the platform imports `app` from
this module. No application code is duplicated.
"""

from app.main import app

# Vercel looks for a module-level object named `app` (or `handler`).
# Re-exporting it here is the whole job of this file.
__all__ = ["app"]
