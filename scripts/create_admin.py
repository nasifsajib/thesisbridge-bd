"""
scripts/create_admin.py
-----------------------
Create (or repair) the administrator account.

Run it once, from the project folder, after sql/002_admin.sql has been run:

    .\\.venv\\Scripts\\python.exe scripts/create_admin.py --password "..."

What it does, in order:

  1. Checks that the `is_admin` column exists. If not, it stops and tells you
     to run sql/002_admin.sql first, instead of failing with a cryptic error.
  2. Creates the Supabase Auth user if the email is new, or resets the
     password if the account already exists. The password is hashed by
     Supabase inside auth.users - it is never written to any file here.
  3. Upserts the matching row in public.profiles with is_admin = true.

Why a script instead of a hardcoded account in the code?
  A password in the source is readable by anyone with the repository, and it
  stays in git history forever. This script creates a REAL account: the
  password exists only as a bcrypt hash in Supabase, exactly like a student's.
  Re-running the script is also how you change the password later.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DEFAULT_EMAIL = "admin@thesisbridge.bd"
DEFAULT_NAME = "Administrator"


def admin_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        sys.exit(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.\n"
            "Copy .env.example to .env and fill in the three Supabase values."
        )

    # The service-role key is required: creating auth users and writing an
    # is_admin flag are operations the browser must never be able to do.
    return create_client(url, key)


def check_column(db) -> None:
    """Fail early, with instructions, when sql/002_admin.sql has not run."""
    try:
        db.table("profiles").select("is_admin").limit(1).execute()
    except APIError as exc:
        if exc.code == "42703":  # undefined column
            sys.exit(
                "The profiles.is_admin column does not exist yet.\n"
                "Open the Supabase dashboard -> SQL Editor -> paste the file\n"
                "sql/002_admin.sql -> Run. Then run this script again."
            )
        raise


def find_user(db, email: str):
    """Return the existing auth user with this email, or None."""
    page = 1
    while True:
        users = db.auth.admin.list_users(page=page, per_page=200)

        if not users:
            return None

        for user in users:
            if (getattr(user, "email", "") or "").lower() == email.lower():
                return user

        if len(users) < 200:
            return None

        page += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the admin account.")
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument(
        "--password",
        default=os.environ.get("ADMIN_PASSWORD", ""),
        help="Password for the admin account (or set ADMIN_PASSWORD).",
    )
    parser.add_argument("--name", default=DEFAULT_NAME)
    args = parser.parse_args()

    email = args.email.strip().lower()
    password = args.password

    if not password:
        sys.exit("Pass --password \"...\" (or set ADMIN_PASSWORD in .env).")

    if len(password) < 8:
        sys.exit("Supabase requires at least 8 characters.")

    db = admin_client()
    check_column(db)

    # ---- 1. the auth user -------------------------------------------------
    user = find_user(db, email)

    if user is None:
        created = db.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                # No SMTP is configured, so the account must be confirmed
                # immediately or login would be impossible.
                "email_confirm": True,
            }
        )
        user_id = created.user.id
        print(f"  created auth user   {email}")
    else:
        user_id = user.id
        # Re-running with a new --password is how the password is changed.
        db.auth.admin.update_user_by_id(user_id, {"password": password})
        print(f"  updated auth user   {email}")

    # ---- 2. the profile row ----------------------------------------------
    db.table("profiles").upsert(
        {
            "id": user_id,
            "name": args.name,
            "email": email,
            "university": None,
            "department": None,
            "student_id": None,
            "interest": "Administrator",
            "is_admin": True,
        },
        on_conflict="id",
    ).execute()

    # ---- 3. read it back and report --------------------------------------
    rows = (
        db.table("profiles")
        .select("id,email,name,is_admin")
        .eq("id", user_id)
        .execute()
        .data
    )

    if not rows or not rows[0].get("is_admin"):
        sys.exit("The profile was written but is_admin is still false. Check the SQL file.")

    print(f"  profile flagged     is_admin = true")
    print(f"\nAdministrator ready: {email}")
    print("Password is stored hashed in Supabase Auth (not in any file).")
    print("Sign in at /admin.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
