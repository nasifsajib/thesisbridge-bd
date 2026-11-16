# ThesisBridge BD — Work History (Backend)

> **What this file is:** a running, honest record of the backend work — what was
> built, why, how it works, what has been verified, and what is still missing.
> New work is appended to the **Session log** at the bottom.
>
> Related files: `SETUP.md` (how to install/deploy) · `README.md` (project report)
> · `sql/001_create_tables.sql` (database) · `app/` (Python code).

---

## 1. Objective

Add a real backend and database to the existing static ThesisBridge BD site.

| Requirement from the user | How it is met |
| --- | --- |
| Backend in Python | FastAPI, package `app/` |
| Database in Supabase | PostgreSQL tables in `sql/001_create_tables.sql`, accessed with `supabase-py` |
| Simple code, no shortcuts | Every file has comments; no custom JWT/ORM magic; explicit SQL and explicit field mapping |
| Every portion commented | Docstrings + inline comments in every backend file and in `public/js/api.js` |
| Connect all pages | `public/js/api.js` + `TB.ready` + edits in `main.js` and the 5 feature modules |
| Deploy on Vercel (teacher requirement) | FastAPI entrypoint `app/main.py`, static site in `public/`, `.python-version`, `vercel.json` |
| Explainable to a teacher | `SETUP.md` sections 4, 6, 7 + this file |

---

## 2. Current status

| # | Task | Status |
| --- | --- | --- |
| 1 | Export prototype data to `seed/content.json` (exact counts verified) | ✅ Done |
| 2 | Move static site into `public/` (Vercel layout) | ✅ Done |
| 3 | Write PostgreSQL schema + RLS (`sql/001_create_tables.sql`) | ✅ Done |
| 4 | Write content seeder (`scripts/seed_supabase.py`) | ✅ Done |
| 5 | Write FastAPI backend (`app/`) | ✅ Done |
| 6 | Connect the frontend (`public/js/api.js`, module boot changes) | ✅ Done |
| 7 | Local syntax + import + route + error-path checks | ✅ Done (see §11) |
| 8 | Create the Supabase project and run the SQL | ✅ Done |
| 9 | Run the seeder against the real project | ✅ Done — all 9 counts OK |
| 10 | End-to-end test: signup → bookmark → reload → logout → login | ✅ Done — 57 API checks + browser run |
| 11 | Deploy to Vercel and test the live URL | ⏳ Next |
| 12 | Update the frontend copy + README report for the new architecture | ✅ Done |

Legend: ✅ done · 🟡 in progress · ⏳ pending · ❌ blocked.

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  BROWSER                                                         │
│  public/*.html + css + js                                        │
│    js/data.js   → offline fallback content (still shipped)       │
│    js/main.js   → UI core: state, modals, toasts, auth forms     │
│    js/api.js    → API bridge: content, auth, saved-state sync    │
│    js/research.js / supervisors.js / publication.js /            │
│       resources.js / network.js → wait for TB.ready, then render │
└───────────────────────────┬──────────────────────────────────────┘
                            │ fetch("/api/...") + Bearer token
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  PYTHON BACKEND (FastAPI)  app/                                  │
│   routers/content.py    public reading data                      │
│   routers/auth.py       signup / login / me                      │
│   routers/user_state.py bookmarks, roadmap, checklist, profile   │
│   routers/requests.py   connection requests                      │
│   dependencies.py       verifies the Bearer token                │
│   database.py           two Supabase clients                     │
└───────────────────────────┬──────────────────────────────────────┘
                            │ supabase-py (HTTPS)
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  SUPABASE                                                        │
│   PostgreSQL (16 tables, RLS policies)                           │
│   Auth (bcrypt password hashing, issues access tokens)           │
└──────────────────────────────────────────────────────────────────┘
```

Deployment view (Vercel):

| URL | Served by |
| --- | --- |
| `/`, `/research.html`, `/css/...`, `/js/...` | static files from `public/` |
| `/api/...` | the single Python function built from `app/main.py` |

---

## 4. Backend files — what each one does

### `app/__init__.py`
Declares the `app` package. No logic. Explains the two run commands
(`uvicorn` locally, Vercel automatically).

### `app/config.py`
Reads the environment **once**:

- `load_dotenv()` loads `.env` locally; on Vercel it does nothing (no file).
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
- `CORS_ORIGINS` (comma-separated, default `*`).
- `missing_settings()` → list of unset variable names.
- `ensure_settings()` → raises `ConfigurationError` with a human-readable
  message instead of a stack trace.
- `class ConfigurationError(RuntimeError)` → caught in `main.py` and returned
  as **HTTP 503** with the same readable message.

### `app/database.py`
Two lazily-created, reused clients:

| Function | Key | Used for |
| --- | --- | --- |
| `get_auth_client()` | anon | Supabase Auth calls (`sign_in_with_password`, `get_user`) |
| `get_admin_client()` | service_role | table reads/writes + `auth.admin.create_user` |

Why two: Auth calls should not run with more power than necessary, and the
service role key must never be used for browser-facing auth operations. Both
are created only on first use (a simple singleton), so a warm serverless
function reuses them.

### `app/dependencies.py`
FastAPI dependencies (functions FastAPI runs before a route):

- `_extract_token(header)` → parses `Authorization: Bearer <token>`.
- `get_current_user()` → 401 when the token is missing/invalid; else returns
  `{id, email, token}` after `auth.get_user(token)` verifies it with Supabase.
- `get_optional_user()` → returns `None` instead of raising; used by the public
  connection-request endpoint so guests and members can both send requests.

`ConfigurationError` is re-raised (not converted to 401) so a missing `.env`
is reported as a setup problem.

### `app/schemas.py`
All Pydantic models. Two jobs: validate input, shape output.

- `CamelModel` → `alias_generator=to_camel`, `populate_by_name=True`.
  Database is snake_case, JSON is camelCase, both work in Python.
- Content models: `Category`, `ResearchIdea`, `Supervisor`, `Resource`,
  `PublicationGuide` (+ `GuideSection`), `RoadmapStep` (+ `RoadmapResource`),
  `Faq`, `ChecklistItem`, `ContentBundle`.
- Auth models: `SignupRequest` (password 8–72 chars because bcrypt uses 72
  bytes), `LoginRequest`, `UserOut`, `AuthResponse` (`accessToken`), 
  `ProfileUpdate`.
- State models: id-list payloads for each saved list, `ConnectionRequestCreate`,
  `ConnectionRequestOut` (maps DB `created_at` → JSON `date`), and
  `UserStateResponse` (everything the frontend stores, in one call).

### `app/routers/content.py`
Public reading endpoints. Key helpers:

- `_fetch(table, order=...)` → all rows, optionally ordered.
- `_single(table, id, id_column="id")` → one row or 404 (uses `limit(1)`, not
  `maybe_single()`, so behaviour is stable across supabase-py versions).
- `_safe_search(text)` → strips `, ( ) *` so user text cannot break or inject
  into a PostgREST `or_()` filter.

Endpoints: `/content` (the whole bundle), `/ideas` (+ filters/sort/pagination),
`/ideas/{id}`, `/supervisors`, `/supervisors/{id}`, `/resources`,
`/resources/{id}`, `/publication-guides`, `/publication-guides/{id}`,
`/roadmap`, `/faqs`, `/checklist`.

`/content` exists so the frontend can replace `window.TB_DATA` with one call
instead of eight, exactly preserving the old rendering logic.

### `app/routers/auth.py`
- `_clean(value)` → empty form fields become `None`.
- `_profile_for(user_id)` → read a profile row.
- `_ensure_profile(user_id, email, metadata)` → create a minimal profile for
  accounts made directly in the Supabase dashboard; used by login and `/me`.
- `_token_from_session(result)` → reads `session.access_token`; if there is no
  session (unconfirmed email), returns 403 with a clear message.
- `POST /signup` → `admin.auth.admin.create_user({..., email_confirm: True})`,
  insert `profiles`, then `sign_in_with_password` and return the token. If the
  profile insert fails, the auth user is deleted again (rollback).
- `POST /login` → `sign_in_with_password`; wrong credentials produce one
  generic 401 message (does not reveal whether the email exists).
- `GET /me` → profile of the token owner; repairs a missing profile row.

### `app/routers/user_state.py`
- `_profile(user_id)` → 404 if the profile is missing.
- `_ids_from(db, table, column, user_id)` → read one id column.
- `_replace_rows(db, table, user_id, id_column, ids)` → the core sync routine:
  1. **upsert** the requested rows,
  2. **delete** rows not in the list (`not_.in_`).
  Step 1 before step 2 means a bad id cannot delete existing data.
- `GET /state` → profile + all five lists + connection requests in one call.
- `PUT /bookmarks/ideas`, `/bookmarks/supervisors`, `/roadmap`, `/read-guides`,
  `/checklist` → replace one list; returns the canonical id list.
- `PUT /profile` → updates only the fields that were sent
  (`model_dump(exclude_unset=True)`), blank optional fields become `NULL`.

### `app/routers/requests.py`
- `POST /connection-requests` → public; validates that the supervisor exists,
  stores `user_id` when a token is present, otherwise `NULL` for guests.
  Uses `upsert(on_conflict="user_id,supervisor_id")` so a member cannot create
  duplicates.
- `GET /me/connection-requests` → my requests, newest first.
- `DELETE /me/connection-requests/{supervisor_id}` → withdraw one.

### `app/main.py`
- Creates `app = FastAPI(...)` (the name Vercel looks for).
- Adds `CORSMiddleware` (`allow_credentials=False` because we use Bearer
  tokens, not cookies).
- Registers four routers under `/api`, `/api/auth`, `/api/me`, `/api`.
- `GET /api/health` → always 200; reports `databaseConfigured` and
  `missingSettings`, so it is the first URL to open when something is wrong.
- Exception handler for `ConfigurationError` → 503 + readable detail.
- Startup log warns about missing keys.
- `GET /` → small local-development message (Vercel serves the website at `/`).

### `scripts/seed_supabase.py`
- Inserts the content from `seed/content.json` with `upsert` (safe to re-run).
- One explicit conversion function per table (`category_rows`,
  `idea_rows`, ...) so the JSON→column mapping is visible and explainable.
- `filter_options` stores seven small vocabularies in one table
  (`difficulty`, `type`, `technology`, `quiz_technology`, `university`,
  `department`, `expertise`) with a `kind` column, instead of seven tables.
- Categories are inserted **before** ideas because `research_ideas.category`
  is a foreign key to `categories(name)`.
- Finishes with a row-count verification against the expected numbers.

---

## 5. Database design (16 tables)

### Reference tables
| Table | Purpose | Keys |
| --- | --- | --- |
| `categories` | filter chips (AI, ML, ...) | PK `name` (text) |
| `filter_options` | seven vocabularies in one table | PK `id`, unique `(kind, value)` |

### Public content tables
| Table | Rows seeded | Notes |
| --- | --- | --- |
| `research_ideas` | 20 | `technologies`, `universities`, `tags`, `keywords` are `text[]`; `category` FK |
| `supervisors` | 12 | arrays for interests/expertise/areas/publications; `accepting` boolean |
| `resources` | 20 | `learn_points text[]`, optional `url` |
| `publication_guides` | 7 | `sections jsonb`, `tips text[]`, `position` |
| `roadmap_steps` | 8 | `actions text[]`, `resources jsonb` |
| `faqs` | 8 | `question`, `answer` |
| `journal_checklist_items` | 8 | `position` keeps UI order |

### User tables
| Table | Key | Cascade |
| --- | --- | --- |
| `profiles` | PK/FK `id` → `auth.users(id)` | deleting an auth user deletes the profile |
| `idea_bookmarks` | PK `(user_id, idea_id)` | cascade from both sides |
| `saved_supervisors` | PK `(user_id, supervisor_id)` | cascade |
| `roadmap_progress` | PK `(user_id, step_id)` | cascade |
| `read_guides` | PK `(user_id, guide_id)` | cascade |
| `checklist_progress` | PK `(user_id, item_id)` | cascade |
| `connection_requests` | PK `id` uuid, unique `(user_id, supervisor_id)` | `user_id` nullable for guests, `ON DELETE SET NULL` |

### Row Level Security
- Content tables: `select` allowed to `anon` and `authenticated`; writes only
  possible with the service role (no insert/update/delete policy).
- User tables: `auth.uid() = user_id` for select/insert/update/delete.
- `profiles`: users may read and update only their own row.
- `connection_requests`: users may read/delete their own; guests cannot insert
  directly — the backend inserts guest rows with the service role.
- The Python backend uses the **service role** key, which bypasses RLS by
  design; RLS is the second line of defence if the browser ever talks to
  Supabase directly with the anon key.

Indexes: `research_ideas(category)`, `(difficulty)`, `(type)`,
`supervisors(university)`, `connection_requests(user_id)`.

Trigger: `profiles_touch_updated_at` → `public.touch_updated_at()` sets
`updated_at = now()` on every profile update.

---

## 6. Authentication flow

```
SIGN UP
browser form → POST /api/auth/signup
  → admin.auth.admin.create_user({email, password, email_confirm: true})
      Supabase hashes the password (bcrypt) inside auth.users
  → insert into public.profiles
  → auth.sign_in_with_password() → access_token
  → browser stores ONLY the token (localStorage key `tb_token`)

LOGIN
browser → POST /api/auth/login
  → auth.sign_in_with_password() → Supabase compares the bcrypt hash
  → backend loads/repairs profile → returns token + profile
  → api.js calls GET /api/me/state and hydrates local lists

PROTECTED REQUEST
Authorization: Bearer <token>
  → get_current_user() → auth.get_user(token)
  → 401 if missing, expired or invalid

LOGOUT
api.js clears `tb_token`, clears the local copies of the five lists and
`tb_user`, so the next visitor on that computer cannot see them.
```

Decisions: Supabase Auth was chosen by the user; passwords are never handled by
our Python code; admin `create_user` avoids the email-confirmation blocker
(no SMTP configured); no refresh flow (1-hour token, documented limitation).

---

## 7. Saved-state sync (frontend ↔ backend)

Frontend keys (unchanged from the prototype) and their endpoint:

| localStorage key | Endpoint | JSON field |
| --- | --- | --- |
| `tb_bookmarks` | `PUT /api/me/bookmarks/ideas` | `ideaIds` |
| `tb_savedSupervisors` | `PUT /api/me/bookmarks/supervisors` | `supervisorIds` |
| `tb_roadmap` | `PUT /api/me/roadmap` | `stepIds` |
| `tb_readGuides` | `PUT /api/me/read-guides` | `guideIds` |
| `tb_checklist` | `PUT /api/me/checklist` | `itemIds` |
| `tb_connectRequests` | `POST` / `DELETE /api/connection-requests...` | diff-synced |

Mechanism in `public/js/api.js`:

1. `TB.state.set` is wrapped: it writes localStorage first (instant UI, same
   event `tb:change` as before), then sends the whole list to the API.
2. `suppressSync` prevents echoing server data back during hydration.
3. Guests: only localStorage (no token → no API write).
4. Connection requests are diffed (new supervisor → POST, removed → DELETE)
   and work for guests too.
5. `TB.ready` = content loaded + user state hydrated; every feature module
   boots from it, so the first render uses database data.
6. API base: `file://` and `localhost` → `http://127.0.0.1:8000`; production →
   same origin (`""`); `window.TB_API_BASE` can override.

---

## 8. Why the site moved into `public/`

Vercel's FastAPI project layout is:

- `app/main.py` → the serverless function (Vercel looks for a `FastAPI` object
  named `app`),
- `public/` → static assets served at the domain root.

So `assets/`, `css/`, `js/` and all `.html` files were moved into `public/`,
keeping every relative link (`css/style.css`, `js/data.js`, ...) working.
`seed/`, `sql/`, `scripts/`, `app/`, `requirements.txt`, `.env.example`,
`.python-version`, `vercel.json` stay at the root and are **not** served.

---

## 9. Verification log

Environment: Windows, Python 3.14.7, Node 24.19.0, FastAPI 0.163.1,
Pydantic 2.14.3, supabase-py 2.34.1.

| Check | Command | Result |
| --- | --- | --- |
| Python syntax | `python -m compileall -q app scripts` | PASS |
| JS syntax (7 files) | `node --check public/js/*.js` | PASS |
| Dependencies install on Python 3.14 | `pip install -r requirements.txt` | PASS |
| App import | `from app.main import app` | PASS |
| Route registration | `app.openapi()["paths"]` | 26 API paths |
| Health, no env | `GET /api/health` | 200, `databaseConfigured: false` |
| Content, no env | `GET /api/content` | 503 with readable missing-variable message |
| Protected route, no token | `GET /api/me/state` | 401 "Please log in to continue." |
| Login, no env | `POST /api/auth/login` | 503 (setup problem, not "wrong password") |
| Signup validation | `POST /api/auth/signup` with bad email/short password | 422 |
| Browser, home page | 6 pages loaded in Chromium | 20 idea cards, 12 supervisor cards, 8 roadmap steps, 8 FAQs; no JS errors |
| Browser, other pages | research / supervisors / publication / resources / about | 20 ideas, 12 supervisors, 7 guides + 8 checklist items, 20 resources, 8 FAQs; no JS errors |
| Browser, sign-up modal | click `Get Started` | modal opens, 10 form controls, name/email/password all present |
| Browser, bookmark | `TB.toggleBookmark(1)` twice | localStorage `[1]` → `[]`, badge updates |
| Browser, roadmap | click a step + "Mark as Complete" | `tb_roadmap = [1]`, header shows "13% Complete" |
| Browser, checklist | tick first item | `tb_checklist = ["q1"]` |
| Browser, login with API unconfigured | submit login form | readable error toast, still logged out (no crash) |
| Browser, API fallback | API returns 503 | page renders from `js/data.js`, one console warning, no JS crash |
| **Live: `/api/health` with real keys** | uvicorn + `.env` | 200 · `databaseConfigured: true` · `missingSettings: []` |
| **Live: SQL schema** | `001_create_tables.sql` in the SQL Editor | `Success. No rows returned` — 16 tables created |
| **Live: seeder** | `python scripts/seed_supabase.py` | 9 tables seeded; every expected count matched (9/58/20/12/20/7/8/8/8) |
| **Live: API suite** | temporary probe, 57 assertions | **57 passed, 0 failed** |
| **Live: browser, home** | Chromium, API running | 9 categories · 20 ideas · 12 supervisors · 8 steps · 8 FAQs, zero console warnings (= DB, not fallback) |
| **Live: browser, sign-up** | real form → `POST /api/auth/signup` | toast "Profile created successfully.", 856-char token, profile row in `profiles` |
| **Live: browser, saving** | bookmark + roadmap + checklist | `idea_bookmarks [1]`, `roadmap_progress [1]`, `checklist_progress ["q1"]`, "13% Complete" |
| **Live: browser, server-side restore** | deleted the three localStorage lists, then reloaded | all three came back from PostgreSQL: `[1]`, `[1]`, `["q1"]` |
| **Live: browser, logout** | navbar logout button | token `null`, every list `[]`, `tb_user` cleared |
| **Live: browser, login** | login form | token + all lists restored, toast "Welcome back, Browser." |
| **Live: browser, connection request** | profile modal → Connect → Send Request | row in `connection_requests` with `user_id` set, `status = pending` |
| **Live: guest request** | `POST /api/connection-requests` without a token | 201, stored with `user_id = NULL` |
| **Live: test data cleanup** | deleted `e2e-*` / `browser-*` accounts | all 7 user tables back to 0 rows; content tables untouched |
| **Live Supabase test** | — | ✅ complete |

The 26 endpoints:

```
GET    /api/health
GET    /api/content
GET    /api/ideas
GET    /api/ideas/{idea_id}
GET    /api/supervisors
GET    /api/supervisors/{supervisor_id}
GET    /api/resources
GET    /api/resources/{resource_id}
GET    /api/publication-guides
GET    /api/publication-guides/{guide_id}
GET    /api/roadmap
GET    /api/faqs
GET    /api/checklist
POST   /api/auth/signup
POST   /api/auth/login
GET    /api/auth/me
GET    /api/me/state
PUT    /api/me/bookmarks/ideas
PUT    /api/me/bookmarks/supervisors
PUT    /api/me/roadmap
PUT    /api/me/read-guides
PUT    /api/me/checklist
PUT    /api/me/profile
POST   /api/connection-requests
GET    /api/me/connection-requests
DELETE /api/me/connection-requests/{supervisor_id}
```

---

## 10. Decisions and reasons

| Decision | Alternative | Why this one |
| --- | --- | --- |
| FastAPI | Flask | User chose it; automatic validation + `/docs` is easy to demo |
| Supabase Auth | own users table + bcrypt + JWT | User chose it; less custom crypto to explain and defend |
| `admin.create_user(email_confirm=True)` | normal sign-up | No SMTP configured → normal sign-up accounts could never log in |
| Two clients (anon + service role) | one service-role client everywhere | Auth calls should not hold extra privileges |
| `auth.get_user(token)` per request | decode JWT ourselves | No secret management, revocation works, less code |
| Whole-list `PUT` | per-item POST/DELETE | Frontend already saves whole arrays; idempotent and simple |
| Upsert then delete | delete then insert | A bad id cannot wipe existing data |
| One `/api/content` bundle | one request per list | Keeps the existing synchronous rendering code unchanged |
| camelCase aliases | rename frontend fields | Zero changes to 5 feature modules and the HTML templates |
| Site moved to `public/` | rewrites in `vercel.json` | Vercel's documented FastAPI layout; no path tricks |
| Python 3.14 (`.python-version`) | 3.12 | Matches the local interpreter; Vercel supports 3.14 |
| `seed/content.json` from `js/data.js` | retype data | Exact same 20/12/20/7/8/8/8/58 records, no typos |

---

## 11. Known limitations / open questions

1. Access token lasts 1 hour; no refresh-token rotation in the frontend.
2. Connection requests are stored, not emailed (no SMTP).
3. Matching quiz and its score still run in the browser.
4. No admin panel; content changes = SQL or re-run the seeder.
5. Guests' connection requests have `user_id = NULL`; they cannot see them
   after clearing the browser.
6. Supabase free plan pauses after ~7 days of inactivity.
7. `research_ideas.category` is a FK to `categories(name)`: adding a category
   later needs a row in `categories` first.

---

## 12. Next steps (in order)

Done already: ✅ credentials + `.env` · ✅ schema · ✅ seeding · ✅ local
end-to-end test (57 API checks + full browser run).

Still to do:

1. **Push to GitHub** (the folder is not a git repository yet):
   `git init`, `git add .`, commit, create the repo, push.
   `.env` is gitignored, so the keys do **not** go to GitHub.
2. **Import in Vercel** → framework preset *Other* → no build command.
3. **Add the environment variables** in Vercel (Production + Preview):
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
   optionally `CORS_ORIGINS`.
4. **Deploy**, then open `https://<project>.vercel.app/api/health` and check
   `databaseConfigured: true`.
5. **Repeat the browser test on the live URL**: signup → bookmark → reload →
   logout → login → connection request.
6. Add the live URL to `README.md` and append the final session here.

---

## 13. Session log

### 2026-11-16 — Session 1: backend created

**Done**
- Inspected the frontend: 20 ideas, 12 supervisors, 20 resources, 7 guides,
  8 roadmap steps, 8 FAQs, 8 checklist items; 8 localStorage keys.
- Exported `js/data.js` to `seed/content.json` with a temporary Node script
  (deleted afterwards). Counts verified against the prototype, including
  58 filter options.
- Moved the static site into `public/`; kept relative paths intact.
- Wrote and ran `sql/001_create_tables.sql`: 16 tables, indexes, RLS policies,
  `touch_updated_at` trigger.
- Wrote the `app/` package (config, database, dependencies, schemas, four
  routers, main). Fixed `_ensure_profile` to accept `(user_id, email, metadata)`
  instead of a fake user object.
- Wrote `scripts/seed_supabase.py` (explicit row builders, batched upserts,
  count verification).
- Wrote `requirements.txt`, `.env.example`, `.gitignore`, `.python-version`,
  `vercel.json`.
- Wrote `public/js/api.js`: API base detection, `request()`, `ApiError`,
  content loading with `data.js` fallback, `TB.state.set` wrapper, hydration,
  `TB.auth.login/signup/logout`, `TB.ready`.
- Rewired `main.js`: login/signup call the API; logout uses `TB.auth.logout`;
  profile and connection-request texts no longer say "demo"; boot waits for
  `TB.ready`. Fixed a real bug: `form.name` is the form's own property, so
  sign-up now uses `form.elements.name`.
- Updated boot in `research.js`, `supervisors.js`, `publication.js`,
  `resources.js`, `network.js` to wait for `TB.ready`.
- Added `<script src="js/api.js" defer>` after `js/main.js` in all six pages.
- Verified: Python compile, JS syntax, dependency install, app import,
  26 routes, health/401/422/503 behaviour without credentials.
- Wrote `SETUP.md` (Supabase, local run, architecture for the viva, Vercel,
  API reference, troubleshooting, limitations).
- Created this `WORK_HISTORY.md`.

**Blocked on**
- No Supabase project credentials yet → cannot run the SQL, seed, or test the
  real database.

**Next session**
- Run the SQL, seed, and the full end-to-end test (see §12).

### 2026-11-16 — Session 2: wiring finished + browser verification

**Done**
- Finished `public/js/main.js`:
  - both logout buttons now call `TB.auth.logout()` (clears `tb_token` and the
    local copies of the five lists),
  - profile modal subtitle and navbar title no longer say "demo",
  - forgot-password note explains Supabase handling,
  - boot waits for `TB.ready`,
  - **bug fixed:** sign-up used `form.name`, but `form.name` is the form's own
    property, not the name input. Now uses `form.elements.name` (and the same
    pattern for every field), so the form can actually submit.
- Added `<script src="js/api.js" defer>` after `js/main.js` in `index.html`,
  `research.html`, `supervisors.html`, `publication.html`, `resources.html`,
  `about.html` (correct order: data → main → api → feature module).
- Updated copy that was no longer true:
  - `supervisors.js`: connection-request note, success message and toast,
  - `resources.js`: resource detail note,
  - footers on 5 pages, `publication.html` checklist subtitle,
  - `about.html` notice box,
  - `data.js` + `seed/content.json` FAQ about where saved data lives,
  - `docs.html` §1 (EN + BN) and a banner on `docs.html` / `docs2.html`
    explaining that the long sections describe the original prototype.
- Rewrote the relevant parts of `README.md` (English + Bangla): intro,
  technology table, file tree, data-door section, how to run, limitations,
  plus links to `SETUP.md` and `WORK_HISTORY.md`.
- Created `.venv`, installed `requirements.txt` on Python 3.14.7
  (FastAPI 0.163.1, Pydantic 2.14.3, supabase-py 2.34.1).
- Ran the app with `TestClient` and with real `uvicorn` + `http.server`.

**Browser evidence (Chromium, API intentionally unconfigured)**
- Home: 20 idea cards, 12 supervisor cards, 8 roadmap steps, 8 FAQs.
- research.html: 20 cards · supervisors.html: 12 · publication.html: 7 guides
  + 8 checklist items · resources.html: 20 · about.html: 8 FAQs.
- Sign-up modal opens through the real navbar button; 10 controls present.
- Bookmark toggle writes `[1]` then `[]`; roadmap step 1 → `tb_roadmap = [1]`
  and header "13% Complete"; checklist tick → `tb_checklist = ["q1"]`.
- Login submit with the API unconfigured shows a readable toast, stays logged
  out, no uncaught JS error.
- With `/api/content` returning 503, pages render from `js/data.js` with one
  console warning — the intended fallback.
- Server log confirmed the CORS preflight: `OPTIONS /api/auth/login → 200`.

**Notes**
- A browser tab requested `/health` instead of `/api/health` → 404. The real
  health URL is `/api/health`; nothing to fix.
- `.venv/`, `__pycache__/`, `.env` are covered by `.gitignore`.

**Blocked on**
- Same as session 1: no Supabase credentials, so the SQL, seeder and real
  auth/data test are still pending.

**Next session**
- Fill `.env`, run the SQL, seed, then repeat the browser test against real
  Supabase data and deploy to Vercel.

### 2026-11-16 — Session 3: live Supabase, seeding, two real bugs fixed

**Goal:** turn the "waiting for credentials" state into a working system.

**Credentials**
- Received the project URL and both new-style API keys
  (`sb_publishable_...` and `sb_secret_...`) and wrote them into `.env`
  (gitignored, never served, never in `public/`).
- Verified the publishable key against `/auth/v1/health` → 200 (GoTrue
  v2.197.0), and through `supabase-py` (`sign_in_with_password` answered
  "Invalid login credentials" for a dummy account, which means the key itself
  was accepted).
- Verified the secret key against `/rest/v1/` → 200. The table API answered
  `401 Secret API key required` for the publishable key, which confirmed the
  two keys are different and correctly assigned.
- `GET /api/health` then reported `databaseConfigured: true`, proving
  `app/config.py` reads the new key format correctly.

**Schema**
- `/rest/v1/categories` returned `404 PGRST205 — Could not find the table`,
  which showed the SQL had not been run yet.
- The user ran `sql/001_create_tables.sql` in the Supabase SQL Editor:
  `Success. No rows returned` → 16 tables, indexes, RLS policies, trigger.

**Seeding**
- `python scripts/seed_supabase.py` inserted every content table and the
  verification block reported **OK for all 9**: categories 9,
  filter_options 58, research_ideas 20, supervisors 12, resources 20,
  publication_guides 7, roadmap_steps 8, faqs 8, journal_checklist_items 8.

**Bugs found and fixed (this is why the live test mattered)**

1. **`Faq` could not read its own table.**
   `app/schemas.py` declared `q` / `a` (the shape the browser needs) but the
   PostgreSQL columns are `question` / `answer`, so `GET /api/content`
   raised a Pydantic `ValidationError` and returned 500.
   Fixed with `validation_alias=AliasChoices("question", "q")` and the same
   for the answer: the model now *reads* the database columns and still
   *writes* `q` / `a`, so no frontend file changed.

2. **Database errors escaped as a bare 500.**
   `app/main.py` had a handler for `ConfigurationError` but nothing for
   `postgrest.exceptions.APIError`, so a failed query produced an unhelpful
   "Internal Server Error". Added a handler that returns 503 with a sentence
   that says what to do:
   - `PGRST205` (table missing) → "run sql/001_create_tables.sql";
   - `42501` (permission denied) → "check that
     SUPABASE_SERVICE_ROLE_KEY holds the secret key, not the publishable one";
   - anything else → `Database error (<code>): <message>`.
   Reads `.code` / `.message` directly from the exception (its `args[0]` is
   only a string).

3. **Small UX gap:** the connection-request form asked a logged-in student to
   retype their name and email. `supervisors.js` now prefills both from
   `tb_user` (only possible because accounts are real now).

**API test — 57 assertions, 0 failures** (temporary script, deleted after the
run): content counts, camelCase shape, sign-up, `/auth/me`, 401 without a
token, all five list endpoints, profile partial update (only sent fields
change, blank university → NULL), `/api/me/state` in one call, member and
guest connection requests, withdraw, login round trip, identical 401 message
for a wrong password and an unknown email (no account leak), 422 validation,
and a direct read of the tables with the service role.

**Browser test (Chromium, real API + real database)**
- Home: 9 categories, 20 ideas, 12 supervisors, 8 roadmap steps, 8 FAQs and
  **no** console warning → the data came from PostgreSQL, not `data.js`.
- Sign-up through the real form → "Profile created successfully.", token
  stored, profile row created.
- Bookmark, roadmap step and checklist tick → correct rows in
  `idea_bookmarks`, `roadmap_progress`, `checklist_progress`.
- **Server-side proof:** the three localStorage lists were deleted, then the
  page was reloaded — all three came back from the database.
- Logout cleared the token and every list; login restored them
  ("Welcome back, Browser.").
- Connection request sent through the modal → row in `connection_requests`
  with `user_id` set and `status = pending`; a guest request was stored with
  `user_id = NULL`.
- Uvicorn's log showed the full chain: `/api/content` 200 with 9 table
  queries, `POST /auth/v1/admin/users` 200, `profiles` 201, token 200,
  bookmark upsert 201 + delete `not.in`, `connection_requests` 201.
- Test accounts (`e2e-*`, `browser-*`) and guest requests were deleted
  afterwards: all 7 user tables are back to 0 rows. Content tables untouched.

**Cleanup**
- Temporary verification scripts deleted; test servers stopped (ports 8000
  and 8417 free); `scripts/` still contains only `seed_supabase.py`.

**Next session**
- Deploy to Vercel (GitHub → import → 3 env vars → deploy) and repeat the
  browser test on the live URL.

<!-- Append new sessions below this line. -->
