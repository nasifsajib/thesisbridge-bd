"""
scripts/seed_supabase.py
------------------------
Fills the Supabase content tables with the data extracted from the original
prototype (seed/content.json).

Run it once, after you have created the tables with sql/001_create_tables.sql:

    python scripts/seed_supabase.py

The script is SAFE TO RUN AGAIN:
  - it uses upsert(), which updates a row when the primary key already exists,
  - it never touches user tables (bookmarks, profiles, requests...),
  - so re-seeding content does not delete anybody's saved ideas.
"""

import json
import sys
from pathlib import Path

# The script lives in scripts/, but it imports the `app` package from the
# project root. Adding the root to sys.path makes that import work no matter
# which folder the terminal is currently in.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import missing_settings  # noqa: E402
from app.database import get_admin_client  # noqa: E402

CONTENT_FILE = ROOT / "seed" / "content.json"

# Number of rows sent to Supabase in one network request.
BATCH_SIZE = 100


# ===========================================================================
# 1. Read the JSON file
# ===========================================================================


def load_content() -> dict:
    """Load the exported prototype data from seed/content.json."""
    if not CONTENT_FILE.exists():
        print(f"ERROR: {CONTENT_FILE} was not found.")
        print("Run the export step first (see README / SETUP.md).")
        sys.exit(1)

    with CONTENT_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


# ===========================================================================
# 2. Convert camelCase JSON into snake_case database rows
# ===========================================================================
# Each function is written out by hand on purpose: you can see exactly which
# JSON field becomes which database column.
# ===========================================================================


def category_rows(data: dict) -> list[dict]:
    rows = []

    for position, item in enumerate(data["categories"]):
        rows.append(
            {
                "name": item["name"],
                "short": item.get("short"),
                "icon": item["icon"],
                "position": position,
            }
        )

    return rows


def filter_option_rows(data: dict) -> list[dict]:
    """
    Build the generic filter_options table.

    Each tuple is (database "kind", JSON key).
    """
    kinds = [
        ("difficulty", "difficulties"),
        ("type", "types"),
        ("technology", "technologies"),
        ("quiz_technology", "quizTechnologies"),
        ("university", "universities"),
        ("department", "departments"),
        ("expertise", "expertiseOptions"),
    ]

    rows = []

    for kind, json_key in kinds:
        for position, value in enumerate(data[json_key]):
            rows.append(
                {
                    "kind": kind,
                    "value": value,
                    "position": position,
                }
            )

    return rows


def idea_rows(data: dict) -> list[dict]:
    rows = []

    for item in data["researchIdeas"]:
        rows.append(
            {
                "id": item["id"],
                "title": item["title"],
                "description": item["description"],
                "category": item["category"],
                "area": item["area"],
                "difficulty": item["difficulty"],
                "technologies": item["technologies"],
                "type": item["type"],
                "universities": item["universities"],
                "tags": item["tags"],
                "problem": item["problem"],
                "gap": item["gap"],
                "methodology": item["methodology"],
                "outcome": item["outcome"],
                "keywords": item["keywords"],
                "featured": item["featured"],
            }
        )

    return rows


def supervisor_rows(data: dict) -> list[dict]:
    rows = []

    for item in data["supervisors"]:
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "title": item["title"],
                "university": item["university"],
                "department": item["department"],
                "interests": item["interests"],
                "expertise": item["expertise"],
                "areas": item["areas"],
                "publications": item["publications"],
                "supervision_types": item["supervisionTypes"],
                "accepting": item["accepting"],
                "email": item["email"],
                "office": item["office"],
                "bio": item["bio"],
                "selected_pubs": item["selectedPubs"],
                "supervision_areas": item["supervisionAreas"],
                "suggested_topics": item["suggestedTopics"],
            }
        )

    return rows


def resource_rows(data: dict) -> list[dict]:
    rows = []

    for item in data["resources"]:
        rows.append(
            {
                "id": item["id"],
                "title": item["title"],
                "category": item["category"],
                "type": item["type"],
                "type_icon": item["typeIcon"],
                "level": item["level"],
                "minutes": item["minutes"],
                "description": item["description"],
                "details": item["details"],
                "learn_points": item["learnPoints"],
                "url": item.get("url"),
                "tags": item["tags"],
            }
        )

    return rows


def guide_rows(data: dict) -> list[dict]:
    rows = []

    for position, item in enumerate(data["publicationGuides"]):
        rows.append(
            {
                "id": item["id"],
                "icon": item["icon"],
                "title": item["title"],
                "summary": item["summary"],
                "sections": item["sections"],
                "tips": item["tips"],
                "position": position,
            }
        )

    return rows


def roadmap_rows(data: dict) -> list[dict]:
    rows = []

    for item in data["roadmapSteps"]:
        rows.append(
            {
                "id": item["id"],
                "icon": item["icon"],
                "title": item["title"],
                "explanation": item["explanation"],
                "actions": item["actions"],
                "resources": item["resources"],
            }
        )

    return rows


def faq_rows(data: dict) -> list[dict]:
    """
    FAQs use a plain integer id. We number them 1..8 in JSON order, which
    makes the upsert idempotent (running twice does not duplicate them).
    """
    rows = []

    for index, item in enumerate(data["faqs"]):
        rows.append(
            {
                "id": index + 1,
                "question": item["q"],
                "answer": item["a"],
            }
        )

    return rows


def checklist_rows(data: dict) -> list[dict]:
    rows = []

    for position, item in enumerate(data["journalChecklist"]):
        rows.append(
            {
                "id": item["id"],
                "label": item["label"],
                "position": position,
            }
        )

    return rows


# ===========================================================================
# 3. Write rows to Supabase
# ===========================================================================


def upsert_rows(client, table: str, rows: list[dict], conflict: str) -> None:
    """
    Send `rows` to one table in batches.

    `conflict` is the column (or comma-separated columns) that identifies a
    row, e.g. "id" or "kind,value". Supabase updates the row when it exists
    and inserts it when it does not.
    """
    if not rows:
        print(f"  {table}: nothing to insert")
        return

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        client.table(table).upsert(batch, on_conflict=conflict).execute()

    print(f"  {table}: {len(rows)} rows")


def count_rows(client, table: str) -> int:
    """
    Ask PostgreSQL for COUNT(*) without downloading the rows.

    limit(1) keeps the response small; count="exact" is what returns the total.
    """
    response = (
        client.table(table).select("*", count="exact").limit(1).execute()
    )
    return response.count or 0


# ===========================================================================
# 4. Main
# ===========================================================================


def main() -> None:
    missing = missing_settings()

    if missing:
        print("ERROR: missing environment variables: " + ", ".join(missing))
        print("Copy .env.example to .env and fill in your Supabase keys.")
        sys.exit(1)

    print("Reading", CONTENT_FILE)
    data = load_content()

    print("Connecting to Supabase...")
    client = get_admin_client()

    # A quick SELECT proves the URL, keys and table names are all correct
    # before we start writing anything.
    try:
        client.table("categories").select("name").limit(1).execute()
    except Exception as exc:
        print("ERROR: could not read the categories table.")
        print("Did you run sql/001_create_tables.sql in the Supabase SQL Editor?")
        print("Details:", exc)
        sys.exit(1)

    print("Seeding content tables...")

    # Order matters: research_ideas.category is a foreign key to categories,
    # so categories must exist first.
    upsert_rows(client, "categories", category_rows(data), "name")
    upsert_rows(client, "filter_options", filter_option_rows(data), "kind,value")
    upsert_rows(client, "research_ideas", idea_rows(data), "id")
    upsert_rows(client, "supervisors", supervisor_rows(data), "id")
    upsert_rows(client, "resources", resource_rows(data), "id")
    upsert_rows(client, "publication_guides", guide_rows(data), "id")
    upsert_rows(client, "roadmap_steps", roadmap_rows(data), "id")
    upsert_rows(client, "faqs", faq_rows(data), "id")
    upsert_rows(
        client,
        "journal_checklist_items",
        checklist_rows(data),
        "id",
    )

    # ---- Verification ---------------------------------------------------
    print("\nVerification (row counts in Supabase):")

    expected = {
        "categories": 9,
        "filter_options": 58,
        "research_ideas": 20,
        "supervisors": 12,
        "resources": 20,
        "publication_guides": 7,
        "roadmap_steps": 8,
        "faqs": 8,
        "journal_checklist_items": 8,
    }

    all_good = True

    for table, wanted in expected.items():
        actual = count_rows(client, table)
        status = "OK" if actual == wanted else "MISMATCH"
        if actual != wanted:
            all_good = False
        print(f"  {table:<26} expected {wanted:>3}   found {actual:>3}   {status}")

    if all_good:
        print("\nDone. Every content table is ready.")
    else:
        print("\nSome counts differ. Check the errors above, then run again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
