"""
app/routers/requests.py
-----------------------
The "Connect with a supervisor" flow.

    POST   /api/connection-requests                  send a request
    GET    /api/me/connection-requests               list my requests
    DELETE /api/me/connection-requests/{supervisor}  withdraw a request

Sending is public on purpose: the website lets a visitor fill the form
before creating an account. When a logged-in member sends it, we attach
their user id, which is what makes the request appear in "My requests".
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_admin_client
from app.dependencies import get_current_user, get_optional_user
from app.schemas import ConnectionRequestCreate, ConnectionRequestOut

router = APIRouter()


# ===========================================================================
# POST /api/connection-requests
# ===========================================================================


@router.post(
    "/connection-requests",
    response_model=ConnectionRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send a connection request to a supervisor",
)
def create_connection_request(
    payload: ConnectionRequestCreate,
    current_user: dict | None = Depends(get_optional_user),
) -> ConnectionRequestOut:
    db = get_admin_client()

    # ---- Make sure the supervisor exists --------------------------------
    supervisor_rows = (
        db.table("supervisors")
        .select("id")
        .eq("id", payload.supervisor_id)
        .limit(1)
        .execute()
        .data
        or []
    )

    if not supervisor_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That supervisor does not exist.",
        )

    row = {
        "user_id": current_user["id"] if current_user else None,
        "supervisor_id": payload.supervisor_id,
        "name": payload.name.strip(),
        "email": payload.email.lower(),
        "topic": payload.topic.strip(),
        "message": payload.message.strip(),
        "status": "pending",
    }

    # For a logged-in user the table has UNIQUE(user_id, supervisor_id), so
    # upsert() replaces an older request instead of creating a duplicate.
    try:
        response = (
            db.table("connection_requests")
            .upsert(row, on_conflict="user_id,supervisor_id")
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The connection request could not be saved. Please try again.",
        )

    rows = response.data or []

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The connection request was saved but not returned.",
        )

    return ConnectionRequestOut.from_row(rows[0])


# ===========================================================================
# GET /api/me/connection-requests
# ===========================================================================


@router.get(
    "/me/connection-requests",
    response_model=list[ConnectionRequestOut],
    summary="List my connection requests",
)
def list_my_connection_requests(
    current_user: dict = Depends(get_current_user),
) -> list[ConnectionRequestOut]:
    db = get_admin_client()

    response = (
        db.table("connection_requests")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    rows = response.data or []
    return [ConnectionRequestOut.from_row(row) for row in rows]


# ===========================================================================
# DELETE /api/me/connection-requests/{supervisor_id}
# ===========================================================================


@router.delete(
    "/me/connection-requests/{supervisor_id}",
    summary="Withdraw my connection request to one supervisor",
)
def delete_connection_request(
    supervisor_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    db = get_admin_client()

    db.table("connection_requests").delete().eq(
        "user_id", current_user["id"]
    ).eq("supervisor_id", supervisor_id).execute()

    return {"deleted": True, "supervisorId": supervisor_id}
