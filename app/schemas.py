"""
app/schemas.py
--------------
Pydantic models = the "shape" of every request and response.

Two jobs:

1. VALIDATION - FastAPI checks incoming JSON against these models and returns
   a clear HTTP 422 error when a field is missing or invalid.

2. SERIALIZATION - FastAPI converts the data we return into JSON. The frontend
   was written with camelCase names (`studentId`, `supervisorId`), while
   PostgreSQL uses snake_case (`student_id`, `supervisor_id`). `to_camel`
   translates automatically, so the database and the browser can both keep
   their own naming style.

`populate_by_name=True` lets us create a model with either style:
    ResearchIdea(**row)            # row keys are snake_case
    ResearchIdea(title="...", ...) # keyword arguments also work
"""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """
    Base model for every schema in this project.

    - alias_generator=to_camel -> JSON uses camelCase.
    - populate_by_name=True    -> Python code may use snake_case.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ===========================================================================
# 1. CONTENT MODELS (public reading data, identical to the old js/data.js)
# ===========================================================================


class Category(CamelModel):
    name: str
    short: str | None = None
    icon: str


class ResearchIdea(CamelModel):
    id: int
    title: str
    description: str
    category: str
    area: str
    difficulty: str
    technologies: list[str]
    type: str
    universities: list[str]
    tags: list[str]
    problem: str
    gap: str
    methodology: str
    outcome: str
    keywords: list[str]
    featured: int = 0


class Supervisor(CamelModel):
    id: int
    name: str
    title: str
    university: str
    department: str
    interests: list[str]
    expertise: list[str]
    areas: list[str]
    publications: int
    supervision_types: list[str]
    accepting: bool
    email: str
    office: str
    bio: str
    selected_pubs: list[str]
    supervision_areas: list[str]
    suggested_topics: list[str]


class Resource(CamelModel):
    id: int
    title: str
    category: str
    type: str
    type_icon: str
    level: str
    minutes: int
    description: str
    details: str
    learn_points: list[str]
    url: str | None = None
    tags: list[str]


class GuideSection(CamelModel):
    heading: str
    body: str


class PublicationGuide(CamelModel):
    id: str
    icon: str
    title: str
    summary: str
    sections: list[GuideSection]
    tips: list[str]


class RoadmapResource(CamelModel):
    label: str
    url: str


class RoadmapStep(CamelModel):
    id: int
    icon: str
    title: str
    explanation: str
    actions: list[str]
    resources: list[RoadmapResource]


class Faq(CamelModel):
    """
    One question/answer pair.

    The browser renders `q` and `a` (that is the shape the old js/data.js used),
    but the PostgreSQL columns are named `question` and `answer`.
    `validation_alias` lets Pydantic *read* the database row, while the JSON we
    send back still uses `q` and `a`, so no frontend code has to change.
    """

    q: str = Field(validation_alias=AliasChoices("question", "q"))
    a: str = Field(validation_alias=AliasChoices("answer", "a"))


class ChecklistItem(CamelModel):
    id: str
    label: str


class ContentBundle(CamelModel):
    """
    Everything the frontend needs for its first paint, in one response.

    Why one big response? The site rendered all filters, cards and modals from
    one JavaScript object (`window.TB_DATA`). Returning the same object keeps
    the frontend logic untouched and avoids 8 slow round-trips on page load.
    """

    categories: list[Category]
    difficulties: list[str]
    types: list[str]
    technologies: list[str]
    quiz_technologies: list[str]
    universities: list[str]
    departments: list[str]
    expertise_options: list[str]
    research_ideas: list[ResearchIdea]
    supervisors: list[Supervisor]
    resources: list[Resource]
    publication_guides: list[PublicationGuide]
    roadmap_steps: list[RoadmapStep]
    faqs: list[Faq]
    journal_checklist: list[ChecklistItem]


class IdeaListResponse(CamelModel):
    """Paginated response for GET /api/ideas."""

    total: int
    items: list[ResearchIdea]


class SupervisorListResponse(CamelModel):
    """Paginated response for GET /api/supervisors."""

    total: int
    items: list[Supervisor]


class ResourceListResponse(CamelModel):
    """Paginated response for GET /api/resources."""

    total: int
    items: list[Resource]


# ===========================================================================
# 2. AUTH MODELS
# ===========================================================================


class SignupRequest(CamelModel):
    name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    # Supabase stores passwords with bcrypt, which only uses the first 72
    # bytes. The frontend also requires at least 8 characters.
    password: str = Field(min_length=8, max_length=72)
    university: str | None = None
    department: str | None = None
    student_id: str | None = None
    interest: str | None = None


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(CamelModel):
    id: str
    name: str
    email: str
    university: str | None = None
    department: str | None = None
    student_id: str | None = None
    interest: str | None = None
    # False for every normal student. The browser uses it only to decide
    # whether to show the "Admin" link; the real check happens on the server
    # in dependencies.require_admin(), which answers 403 for non-admins.
    is_admin: bool = False


class AuthResponse(CamelModel):
    """
    Returned by sign-up and login.

    The frontend stores `accessToken` in localStorage and sends it back as
    `Authorization: Bearer <token>` on every protected request.
    """

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    university: str | None = None
    department: str | None = None
    student_id: str | None = None
    interest: str | None = None


# ===========================================================================
# 3. PERSONAL STATE MODELS (bookmarks, roadmap, checklist, requests)
# ===========================================================================


class IdeaIdsPayload(CamelModel):
    idea_ids: list[int] = Field(default_factory=list)


class SupervisorIdsPayload(CamelModel):
    supervisor_ids: list[int] = Field(default_factory=list)


class StepIdsPayload(CamelModel):
    step_ids: list[int] = Field(default_factory=list)


class GuideIdsPayload(CamelModel):
    guide_ids: list[str] = Field(default_factory=list)


class ChecklistIdsPayload(CamelModel):
    item_ids: list[str] = Field(default_factory=list)


class ConnectionRequestCreate(CamelModel):
    supervisor_id: int
    name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    topic: str = Field(min_length=1, max_length=300)
    message: str = Field(min_length=20, max_length=5000)


class ConnectionRequestOut(CamelModel):
    id: str
    supervisor_id: int
    name: str
    email: str
    topic: str
    message: str
    status: str
    date: datetime

    @classmethod
    def from_row(cls, row: dict) -> "ConnectionRequestOut":
        """
        Convert one PostgreSQL row into the JSON shape the frontend expects.

        The frontend reads `request.date`, while the table column is called
        `created_at`, so we map it here explicitly.
        """
        return cls(
            id=str(row["id"]),
            supervisor_id=row["supervisor_id"],
            name=row["name"],
            email=row["email"],
            topic=row["topic"],
            message=row["message"],
            status=row["status"],
            date=row["created_at"],
        )


class UserStateResponse(CamelModel):
    """Everything the frontend keeps in localStorage, returned in one call."""

    user: UserOut
    bookmark_idea_ids: list[int]
    saved_supervisor_ids: list[int]
    roadmap_step_ids: list[int]
    read_guide_ids: list[str]
    checklist_item_ids: list[str]
    connection_requests: list[ConnectionRequestOut]


# ===========================================================================
# 6. ADMIN MODELS (only reachable through dependencies.require_admin)
# ===========================================================================


class AdminTopIdea(CamelModel):
    """One row of "most bookmarked ideas" - a simple popularity signal."""

    id: int
    title: str
    bookmarks: int


class AdminOverview(CamelModel):
    """The four cards at the top of the admin dashboard."""

    total_students: int
    total_requests: int
    pending_requests: int
    accepted_requests: int
    declined_requests: int
    total_bookmarks: int
    top_ideas: list[AdminTopIdea]


class AdminStudent(CamelModel):
    """
    One student row in the admin table.

    The five counters are computed by the admin router from the join tables,
    so the page needs no extra requests.
    """

    id: str
    name: str
    email: str
    university: str | None = None
    department: str | None = None
    student_id: str | None = None
    joined_at: str | None = None
    bookmarks: int = 0
    saved_supervisors: int = 0
    roadmap_steps: int = 0
    read_guides: int = 0
    checklist_items: int = 0
    requests: int = 0


class AdminConnectionRequest(CamelModel):
    """
    A connection request as the ADMIN sees it: every row, including guests,
    with the supervisor's name resolved so the table is readable.
    """

    id: str
    user_id: str | None = None
    supervisor_id: int
    supervisor_name: str | None = None
    name: str
    email: str
    topic: str
    message: str
    status: str
    date: str | None = None


class AdminStatusUpdate(CamelModel):
    """
    Body of PUT /api/admin/connection-requests/{id}/status.

    Literal[...] means Pydantic rejects anything else with HTTP 422, so the
    status column can only ever hold these three words.
    """

    status: Literal["pending", "accepted", "declined"]
