"""
app/routers/content.py
----------------------
Public endpoints that serve the reading content:

    GET /api/content               everything in one call (used on page load)
    GET /api/ideas                 paginated idea list with filters
    GET /api/ideas/{idea_id}       one idea
    GET /api/supervisors           paginated supervisor list with filters
    GET /api/supervisors/{id}      one supervisor
    GET /api/resources             paginated resource list with filters
    GET /api/resources/{id}        one resource
    GET /api/publication-guides    the 7 Publication Hub guides
    GET /api/publication-guides/{id}
    GET /api/roadmap               the 8 roadmap steps
    GET /api/faqs                  the 8 questions
    GET /api/checklist             the 8 checklist items

None of these routes need a login: they are the public library.
"""

import re

from fastapi import APIRouter, HTTPException, Query

from app.database import get_admin_client
from app.schemas import (
    ChecklistItem,
    Category,
    ContentBundle,
    Faq,
    IdeaListResponse,
    PublicationGuide,
    ResearchIdea,
    Resource,
    ResourceListResponse,
    RoadmapStep,
    Supervisor,
    SupervisorListResponse,
)

router = APIRouter()


# ===========================================================================
# Small helpers
# ===========================================================================


def _fetch(table: str, *, order: str | None = None) -> list[dict]:
    """
    Read every row of a table with the service-role client.

    `order` is the column name used for sorting, e.g. "position" or "id".
    """
    db = get_admin_client()
    query = db.table(table).select("*")

    if order is not None:
        query = query.order(order)

    response = query.execute()
    return response.data or []


def _safe_search(text: str) -> str:
    """
    Make user text safe to insert into a PostgREST filter.

    PostgREST uses commas and parentheses as filter syntax, so a search for
    "AI, ML (2024)" would break the query. Replacing those characters with
    spaces keeps the search working and cannot inject extra filters.
    """
    return re.sub(r"[,()*]", " ", text).strip()


def _single(table: str, row_id: int | str, id_column: str = "id") -> dict:
    """
    Return one row or raise a clean 404.

    We use limit(1) instead of maybe_single() because the behaviour is the
    same across every supabase-py version: the data is always a list.
    """
    db = get_admin_client()
    response = (
        db.table(table)
        .select("*")
        .eq(id_column, row_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []

    if not rows:
        raise HTTPException(status_code=404, detail=f"No record found in {table}.")

    return rows[0]


# ===========================================================================
# GET /api/content - one call that returns the whole public library
# ===========================================================================


@router.get(
    "/content",
    response_model=ContentBundle,
    summary="All public content in one response",
)
def read_content() -> ContentBundle:
    """
    The old prototype had one `window.TB_DATA` object built from js/data.js.
    This endpoint rebuilds that exact object from PostgreSQL, so every page
    can keep its existing rendering logic.
    """
    categories = _fetch("categories", order="position")
    options = _fetch("filter_options", order="position")

    def values_of(kind: str) -> list[str]:
        """Pick the options of one kind, keeping their stored order."""
        return [row["value"] for row in options if row["kind"] == kind]

    return ContentBundle(
        categories=[Category.model_validate(row) for row in categories],
        difficulties=values_of("difficulty"),
        types=values_of("type"),
        technologies=values_of("technology"),
        quiz_technologies=values_of("quiz_technology"),
        universities=values_of("university"),
        departments=values_of("department"),
        expertise_options=values_of("expertise"),
        research_ideas=[
            ResearchIdea.model_validate(row)
            for row in _fetch("research_ideas", order="id")
        ],
        supervisors=[
            Supervisor.model_validate(row)
            for row in _fetch("supervisors", order="id")
        ],
        resources=[
            Resource.model_validate(row) for row in _fetch("resources", order="id")
        ],
        publication_guides=[
            PublicationGuide.model_validate(row)
            for row in _fetch("publication_guides", order="position")
        ],
        roadmap_steps=[
            RoadmapStep.model_validate(row)
            for row in _fetch("roadmap_steps", order="id")
        ],
        faqs=[Faq.model_validate(row) for row in _fetch("faqs", order="id")],
        journal_checklist=[
            ChecklistItem.model_validate(row)
            for row in _fetch("journal_checklist_items", order="position")
        ],
    )


# ===========================================================================
# Research ideas
# ===========================================================================

# The frontend offers these sort choices. The API understands the same names.
IDEA_SORTS: dict[str, tuple[str, bool]] = {
    # sort name  -> (database column, descending?)
    "recommended": ("featured", True),
    "az": ("title", False),
    "za": ("title", True),
    "diff-asc": ("difficulty", False),
    "diff-desc": ("difficulty", True),
}


@router.get(
    "/ideas",
    response_model=IdeaListResponse,
    summary="Search and filter research ideas",
)
def list_ideas(
    q: str | None = Query(default=None, description="Text search"),
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    type: str | None = Query(default=None),
    technology: str | None = Query(default=None),
    sort: str = Query(default="recommended"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> IdeaListResponse:
    """
    Every filter is optional and they combine with AND, exactly like the
    frontend explorer.
    """
    db = get_admin_client()

    # count="exact" asks PostgreSQL for the total number of matching rows, so
    # the response can say "Showing 20 of 20 ideas".
    query = db.table("research_ideas").select("*", count="exact")

    # --- text search -------------------------------------------------------
    if q:
        search = _safe_search(q)
        if search:
            # or_() means: match ANY of these columns.
            query = query.or_(
                f"title.ilike.%{search}%,"
                f"description.ilike.%{search}%,"
                f"category.ilike.%{search}%,"
                f"area.ilike.%{search}%"
            )

    # --- exact filters -----------------------------------------------------
    if category:
        query = query.eq("category", category)
    if difficulty:
        query = query.eq("difficulty", difficulty)
    if type:
        query = query.eq("type", type)

    # --- array filter ------------------------------------------------------
    # technologies is a text[] column; contains() checks one element.
    if technology:
        query = query.contains("technologies", [technology])

    # --- sorting -----------------------------------------------------------
    column, descending = IDEA_SORTS.get(sort, IDEA_SORTS["recommended"])
    query = query.order(column, desc=descending)

    # --- pagination --------------------------------------------------------
    # range() is inclusive on both ends.
    query = query.range(offset, offset + limit - 1)

    response = query.execute()
    rows = response.data or []

    return IdeaListResponse(
        total=response.count if response.count is not None else len(rows),
        items=[ResearchIdea.model_validate(row) for row in rows],
    )


@router.get(
    "/ideas/{idea_id}",
    response_model=ResearchIdea,
    summary="One research idea",
)
def get_idea(idea_id: int) -> ResearchIdea:
    return ResearchIdea.model_validate(_single("research_ideas", idea_id))


# ===========================================================================
# Supervisors
# ===========================================================================


@router.get(
    "/supervisors",
    response_model=SupervisorListResponse,
    summary="Search and filter supervisors",
)
def list_supervisors(
    q: str | None = Query(default=None),
    university: str | None = Query(default=None),
    department: str | None = Query(default=None),
    area: str | None = Query(default=None),
    expertise: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SupervisorListResponse:
    db = get_admin_client()
    query = db.table("supervisors").select("*", count="exact")

    if q:
        search = _safe_search(q)
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,"
                f"university.ilike.%{search}%,"
                f"department.ilike.%{search}%"
            )

    if university:
        query = query.eq("university", university)
    if department:
        query = query.eq("department", department)
    if area:
        query = query.contains("areas", [area])
    if expertise:
        query = query.contains("expertise", [expertise])

    response = (
        query.order("id").range(offset, offset + limit - 1).execute()
    )
    rows = response.data or []

    return SupervisorListResponse(
        total=response.count if response.count is not None else len(rows),
        items=[Supervisor.model_validate(row) for row in rows],
    )


@router.get(
    "/supervisors/{supervisor_id}",
    response_model=Supervisor,
    summary="One supervisor profile",
)
def get_supervisor(supervisor_id: int) -> Supervisor:
    return Supervisor.model_validate(_single("supervisors", supervisor_id))


# ===========================================================================
# Resources
# ===========================================================================


@router.get(
    "/resources",
    response_model=ResourceListResponse,
    summary="Search and filter the resource library",
)
def list_resources(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ResourceListResponse:
    db = get_admin_client()
    query = db.table("resources").select("*", count="exact")

    if q:
        search = _safe_search(q)
        if search:
            query = query.or_(
                f"title.ilike.%{search}%,"
                f"description.ilike.%{search}%,"
                f"category.ilike.%{search}%"
            )

    if category:
        query = query.eq("category", category)

    response = query.order("id").range(offset, offset + limit - 1).execute()
    rows = response.data or []

    return ResourceListResponse(
        total=response.count if response.count is not None else len(rows),
        items=[Resource.model_validate(row) for row in rows],
    )


@router.get(
    "/resources/{resource_id}",
    response_model=Resource,
    summary="One resource",
)
def get_resource(resource_id: int) -> Resource:
    return Resource.model_validate(_single("resources", resource_id))


# ===========================================================================
# Publication guides, roadmap, FAQ, checklist
# ===========================================================================


@router.get(
    "/publication-guides",
    response_model=list[PublicationGuide],
    summary="All Publication Hub guides",
)
def list_publication_guides() -> list[PublicationGuide]:
    rows = _fetch("publication_guides", order="position")
    return [PublicationGuide.model_validate(row) for row in rows]


@router.get(
    "/publication-guides/{guide_id}",
    response_model=PublicationGuide,
    summary="One Publication Hub guide",
)
def get_publication_guide(guide_id: str) -> PublicationGuide:
    return PublicationGuide.model_validate(_single("publication_guides", guide_id))


@router.get(
    "/roadmap",
    response_model=list[RoadmapStep],
    summary="The research roadmap steps",
)
def list_roadmap() -> list[RoadmapStep]:
    rows = _fetch("roadmap_steps", order="id")
    return [RoadmapStep.model_validate(row) for row in rows]


@router.get(
    "/faqs",
    response_model=list[Faq],
    summary="Frequently asked questions",
)
def list_faqs() -> list[Faq]:
    rows = _fetch("faqs", order="id")
    return [Faq.model_validate(row) for row in rows]


@router.get(
    "/checklist",
    response_model=list[ChecklistItem],
    summary="Journal submission checklist items",
)
def list_checklist() -> list[ChecklistItem]:
    rows = _fetch("journal_checklist_items", order="position")
    return [ChecklistItem.model_validate(row) for row in rows]
