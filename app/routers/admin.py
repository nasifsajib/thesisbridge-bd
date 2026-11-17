"""
app/routers/admin.py
--------------------
The administrator dashboard API. Every route here sits behind
`dependencies.require_admin`, so a normal student receives HTTP 403 even if
they know the URL.

    GET  /api/admin/overview                       totals for the cards
    GET  /api/admin/students                       every student + activity
    GET  /api/admin/connection-requests            the request inbox
    PUT  /api/admin/connection-requests/{id}/status change pending -> accepted

WHY IS EVERYTHING COMPUTED HERE AND NOT IN THE BROWSER?
The browser is allowed to call these routes only with an admin token, but the
counts are built from the protected tables. Doing the work on the server means
the page can be a thin renderer: four requests, no clever client logic, and no
chance of the browser seeing rows it is not allowed to see.

WHY NO NEW ROW LEVEL SECURITY POLICIES?
The backend uses the service-role key, which already bypasses RLS. Adding
"admins can read everything" policies to PostgreSQL would give the browser a
second path into the same data with a different rule set, and two rules that
must stay in agreement is one rule too many. Authorisation is enforced once,
in require_admin().
"""

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Literal

from app.database import get_admin_client
from app.dependencies import require_admin
from app.schemas import (
    AdminConnectionRequest,
    AdminOverview,
    AdminStatusUpdate,
    AdminStudent,
    AdminTopIdea,
)

router = APIRouter()


# ===========================================================================
# Helpers
# ===========================================================================


def _rows(table: str, columns: str = "*") -> list[dict]:
    """
    Read every row of one table with the service-role client.

    The project is small (one class project, tens of rows), so pulling a whole
    small table and counting in Python is simpler and more readable than five
    different SQL aggregate queries. PostgREST returns at most 1000 rows by
    default, which is well above anything this database holds.
    """
    return get_admin_client().table(table).select(columns).execute().data


def _count_by(rows: list[dict], key: str) -> Counter:
    """Count how many times each value appears in one column."""
    return Counter(row.get(key) for row in rows if row.get(key) is not None)


def _supervisor_names() -> dict[int, str]:
    """id -> name, so the request table can show a person instead of a number."""
    return {row["id"]: row["name"] for row in _rows("supervisors", "id,name")}


# ===========================================================================
# 1. Overview - the numbers at the top of the dashboard
# ===========================================================================


@router.get(
    "/overview",
    response_model=AdminOverview,
    summary="Dashboard totals",
)
def overview(admin: dict = Depends(require_admin)) -> AdminOverview:
    """
    Four cards plus a small popularity list.

    `total_students` deliberately counts NON-admin profiles: the administrator
    account is not a student and would otherwise make every count one too
    high, which makes the numbers harder to explain.
    """
    profiles = _rows("profiles", "id,is_admin")
    students = [row for row in profiles if not row.get("is_admin")]

    requests = _rows("connection_requests", "status")
    statuses = Counter(row.get("status") or "pending" for row in requests)

    bookmarks = _rows("idea_bookmarks", "idea_id")
    per_idea = _count_by(bookmarks, "idea_id")

    # Only the five most bookmarked ideas are needed; look their titles up in
    # one query instead of one query per row.
    top_ids = [idea_id for idea_id, _ in per_idea.most_common(5)]
    titles = {}
    if top_ids:
        for row in get_admin_client().table("research_ideas").select(
            "id,title"
        ).in_("id", top_ids).execute().data:
            titles[row["id"]] = row["title"]

    return AdminOverview(
        total_students=len(students),
        total_requests=len(requests),
        pending_requests=statuses.get("pending", 0),
        accepted_requests=statuses.get("accepted", 0),
        declined_requests=statuses.get("declined", 0),
        total_bookmarks=len(bookmarks),
        top_ideas=[
            AdminTopIdea(
                id=idea_id,
                title=titles.get(idea_id, f"Idea #{idea_id}"),
                bookmarks=count,
            )
            for idea_id, count in per_idea.most_common(5)
        ],
    )


# ===========================================================================
# 2. Students - who signed up, and how much they actually used the site
# ===========================================================================


@router.get(
    "/students",
    response_model=list[AdminStudent],
    summary="Every registered student with activity counts",
)
def students(admin: dict = Depends(require_admin)) -> list[AdminStudent]:
    """
    One table row per student, newest first.

    The five counters come from the join tables. They are fetched as whole
    columns and counted in Python (see _count_by), so the query count stays
    fixed at six no matter how many students exist. That is the difference
    between this and a naive loop that queries once per student.
    """
    profiles = [row for row in _rows("profiles") if not row.get("is_admin")]

    bookmarks = _count_by(_rows("idea_bookmarks", "user_id"), "user_id")
    saved = _count_by(_rows("saved_supervisors", "user_id"), "user_id")
    roadmap = _count_by(_rows("roadmap_progress", "user_id"), "user_id")
    guides = _count_by(_rows("read_guides", "user_id"), "user_id")
    checks = _count_by(_rows("checklist_progress", "user_id"), "user_id")
    requests_by_user = _count_by(
        [row for row in _rows("connection_requests", "user_id") if row.get("user_id")],
        "user_id",
    )

    result = [
        AdminStudent(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            university=row.get("university"),
            department=row.get("department"),
            student_id=row.get("student_id"),
            joined_at=row.get("created_at"),
            bookmarks=bookmarks.get(row["id"], 0),
            saved_supervisors=saved.get(row["id"], 0),
            roadmap_steps=roadmap.get(row["id"], 0),
            read_guides=guides.get(row["id"], 0),
            checklist_items=checks.get(row["id"], 0),
            requests=requests_by_user.get(row["id"], 0),
        )
        for row in profiles
    ]

    # Newest first; ISO timestamps sort correctly as plain strings.
    result.sort(key=lambda item: item.joined_at or "", reverse=True)
    return result


# ===========================================================================
# 3. Connection requests - the inbox that used to be invisible
# ===========================================================================


@router.get(
    "/connection-requests",
    response_model=list[AdminConnectionRequest],
    summary="All connection requests, including guests",
)
def connection_requests(
    admin: dict = Depends(require_admin),
    status_filter: Literal["pending", "accepted", "declined"] | None = Query(
        default=None,
        alias="status",
        description="Optional filter: pending, accepted or declined.",
    ),
) -> list[AdminConnectionRequest]:
    """
    The admin sees EVERY request, not just their own.

    This is the endpoint that finally makes `connection_requests.status`
    meaningful. Guests have `user_id = NULL` and are still listed, because a
    request from someone without an account is a real request.
    """
    query = get_admin_client().table("connection_requests").select("*")

    if status_filter is not None:
        query = query.eq("status", status_filter)

    rows = query.order("created_at", desc=True).execute().data
    names = _supervisor_names()

    return [
        AdminConnectionRequest(
            id=row["id"],
            user_id=row.get("user_id"),
            supervisor_id=row["supervisor_id"],
            supervisor_name=names.get(row["supervisor_id"]),
            name=row["name"],
            email=row["email"],
            topic=row["topic"],
            message=row["message"],
            status=row.get("status") or "pending",
            date=row.get("created_at"),
        )
        for row in rows
    ]


@router.put(
    "/connection-requests/{request_id}/status",
    response_model=AdminConnectionRequest,
    summary="Accept or decline one request",
)
def update_request_status(
    request_id: str,
    payload: AdminStatusUpdate,
    admin: dict = Depends(require_admin),
) -> AdminConnectionRequest:
    """
    Move one request between pending, accepted and declined.

    Three details worth knowing:

      * `AdminStatusUpdate` uses Literal[...], so FastAPI itself rejects
        anything that is not one of the three words (HTTP 422). The database
        therefore cannot receive a typo like "acepted".
      * Only the `status` column is written. A mass-assignment bug would need
        a field in the model to be possible, and the model has exactly one.
      * Selecting after the update returns the saved row, so the page can
        redraw the badge from the server's answer instead of guessing.
    """
    db = get_admin_client()

    updated = (
        db.table("connection_requests")
        .update({"status": payload.status})
        .eq("id", request_id)
        .execute()
        .data
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That connection request no longer exists.",
        )

    row = updated[0]
    names = _supervisor_names()

    return AdminConnectionRequest(
        id=row["id"],
        user_id=row.get("user_id"),
        supervisor_id=row["supervisor_id"],
        supervisor_name=names.get(row["supervisor_id"]),
        name=row["name"],
        email=row["email"],
        topic=row["topic"],
        message=row["message"],
        status=row.get("status") or "pending",
        date=row.get("created_at"),
    )
