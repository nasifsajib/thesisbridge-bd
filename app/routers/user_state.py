"""
app/routers/user_state.py
-------------------------
Everything a logged-in user owns: bookmarks, roadmap progress, read guides,
checklist ticks, connection requests and the profile itself.

    GET  /api/me/state                    everything in one call (page load)
    PUT  /api/me/bookmarks/ideas          replace the saved-idea list
    PUT  /api/me/bookmarks/supervisors    replace the saved-supervisor list
    PUT  /api/me/roadmap                  replace the completed-step list
    PUT  /api/me/read-guides              replace the read-guide list
    PUT  /api/me/checklist                replace the checklist list
    PUT  /api/me/profile                  edit name / university / ...

WHY "REPLACE THE WHOLE LIST"?
The frontend already keeps a JavaScript array (for example tb_bookmarks) and
saves the whole array on every click. Accepting the whole array keeps the two
sides identical and makes the API idempotent: sending the same list twice
produces the same result.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_admin_client
from app.dependencies import get_current_user
from app.schemas import (
    ChecklistIdsPayload,
    ConnectionRequestOut,
    GuideIdsPayload,
    IdeaIdsPayload,
    ProfileUpdate,
    StepIdsPayload,
    SupervisorIdsPayload,
    UserOut,
    UserStateResponse,
)

router = APIRouter()


# ===========================================================================
# Helpers
# ===========================================================================


def _profile(user_id: str) -> dict:
    """Return the profile row, or a 404 if the account is inconsistent."""
    db = get_admin_client()
    response = (
        db.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    )
    rows = response.data or []

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please log in again.",
        )

    return rows[0]


def _ids_from(db, table: str, column: str, user_id: str) -> list:
    """Read one id column for a user, e.g. every saved idea_id."""
    response = db.table(table).select(column).eq("user_id", user_id).execute()
    rows = response.data or []
    return [row[column] for row in rows]


def _replace_rows(
    db,
    table: str,
    user_id: str,
    id_column: str,
    ids: list,
) -> None:
    """
    Make the table contain exactly `ids` for this user.

    Order matters:
      1. UPSERT the requested rows first (creates missing ones, keeps existing).
      2. DELETE the rows that are not in the new list.

    If step 1 fails (for example an id that does not exist), nothing has been
    deleted yet, so the user's old data is still safe.
    """
    if ids:
        rows = [{"user_id": user_id, id_column: value} for value in ids]
        try:
            db.table(table).upsert(
                rows,
                on_conflict=f"user_id,{id_column}",
            ).execute()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"One or more values sent for {table} do not exist.",
            )

    delete_query = db.table(table).delete().eq("user_id", user_id)

    if ids:
        # Keep the rows we just upserted; delete every other row.
        delete_query = delete_query.not_.in_(id_column, ids)

    delete_query.execute()


def _unique_ints(values: list[int]) -> list[int]:
    """Remove duplicates and keep a stable order."""
    return sorted(set(values))


def _unique_text(values: list[str]) -> list[str]:
    """Remove duplicates from text ids and keep a stable order."""
    return sorted(set(values))


# ===========================================================================
# GET /api/me/state
# ===========================================================================


@router.get(
    "/state",
    response_model=UserStateResponse,
    summary="All of the logged-in user's saved state",
)
def read_state(current_user: dict = Depends(get_current_user)) -> UserStateResponse:
    db = get_admin_client()
    user_id = current_user["id"]

    profile = _profile(user_id)

    requests_response = (
        db.table("connection_requests")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    request_rows = requests_response.data or []

    return UserStateResponse(
        user=UserOut.model_validate(profile),
        bookmark_idea_ids=_ids_from(db, "idea_bookmarks", "idea_id", user_id),
        saved_supervisor_ids=_ids_from(
            db, "saved_supervisors", "supervisor_id", user_id
        ),
        roadmap_step_ids=_ids_from(db, "roadmap_progress", "step_id", user_id),
        read_guide_ids=_ids_from(db, "read_guides", "guide_id", user_id),
        checklist_item_ids=_ids_from(db, "checklist_progress", "item_id", user_id),
        connection_requests=[
            ConnectionRequestOut.from_row(row) for row in request_rows
        ],
    )


# ===========================================================================
# PUT endpoints - each one replaces one list
# ===========================================================================


@router.put(
    "/bookmarks/ideas",
    summary="Replace the user's saved research ideas",
)
def replace_idea_bookmarks(
    payload: IdeaIdsPayload,
    current_user: dict = Depends(get_current_user),
) -> dict:
    db = get_admin_client()
    ids = _unique_ints(payload.idea_ids)
    _replace_rows(db, "idea_bookmarks", current_user["id"], "idea_id", ids)
    return {"ideaIds": ids}


@router.put(
    "/bookmarks/supervisors",
    summary="Replace the user's saved supervisors",
)
def replace_saved_supervisors(
    payload: SupervisorIdsPayload,
    current_user: dict = Depends(get_current_user),
) -> dict:
    db = get_admin_client()
    ids = _unique_ints(payload.supervisor_ids)
    _replace_rows(db, "saved_supervisors", current_user["id"], "supervisor_id", ids)
    return {"supervisorIds": ids}


@router.put(
    "/roadmap",
    summary="Replace the user's completed roadmap steps",
)
def replace_roadmap(
    payload: StepIdsPayload,
    current_user: dict = Depends(get_current_user),
) -> dict:
    db = get_admin_client()
    ids = _unique_ints(payload.step_ids)
    _replace_rows(db, "roadmap_progress", current_user["id"], "step_id", ids)
    return {"stepIds": ids}


@router.put(
    "/read-guides",
    summary="Replace the user's read Publication Hub guides",
)
def replace_read_guides(
    payload: GuideIdsPayload,
    current_user: dict = Depends(get_current_user),
) -> dict:
    db = get_admin_client()
    ids = _unique_text(payload.guide_ids)
    _replace_rows(db, "read_guides", current_user["id"], "guide_id", ids)
    return {"guideIds": ids}


@router.put(
    "/checklist",
    summary="Replace the user's checklist ticks",
)
def replace_checklist(
    payload: ChecklistIdsPayload,
    current_user: dict = Depends(get_current_user),
) -> dict:
    db = get_admin_client()
    ids = _unique_text(payload.item_ids)
    _replace_rows(db, "checklist_progress", current_user["id"], "item_id", ids)
    return {"itemIds": ids}


# ===========================================================================
# PUT /api/me/profile
# ===========================================================================


@router.put(
    "/profile",
    response_model=UserOut,
    summary="Update the logged-in user's profile",
)
def update_profile(
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> UserOut:
    db = get_admin_client()

    # exclude_unset=True returns only the fields the browser actually sent,
    # so editing the name does not erase the university by accident.
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        return UserOut.model_validate(_profile(current_user["id"]))

    # Replace empty strings with NULL for the optional columns.
    for key in ("university", "department", "student_id", "interest"):
        if key in changes and changes[key] is not None:
            changes[key] = changes[key].strip() or None

    if "name" in changes and not changes["name"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty.",
        )

    db.table("profiles").update(changes).eq("id", current_user["id"]).execute()

    return UserOut.model_validate(_profile(current_user["id"]))
