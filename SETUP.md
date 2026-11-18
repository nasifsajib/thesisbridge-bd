# ThesisBridge BD — Backend Setup Guide

This file explains, step by step, how the **Python (FastAPI) backend** and the
**Supabase database** were added to the website, how to run everything on your
own computer, and how to deploy it on **Vercel**.

Every command is written out in full. Nothing is hidden behind a script you
cannot explain.

---

## 1. What is in the project now?

```
thesisbridge-bd/
├── app/                      ← the Python backend (FastAPI)
│   ├── main.py               ← creates the app, CORS, routers, /api/health
│   ├── config.py             ← reads SUPABASE_URL / keys from .env
│   ├── database.py           ← creates the two Supabase clients
│   ├── dependencies.py       ← "who is logged in?" + "is that user an admin?"
│   ├── schemas.py            ← Pydantic models = shape of JSON in and out
│   └── routers/
│       ├── content.py        ← public content endpoints
│       ├── auth.py           ← signup / login / me
│       ├── user_state.py     ← bookmarks, roadmap, checklist, profile
│       ├── requests.py       ← "connect with a supervisor" requests
│       └── admin.py          ← dashboard data (administrators only)
│
├── public/                   ← the original website (HTML, CSS, JS, assets)
│   ├── index.html            ← Vercel serves this folder at "/"
│   ├── admin.html            ← NEW: administrator dashboard page
│   ├── js/api.js             ← NEW: the bridge between the pages and the API
│   ├── js/admin.js           ← NEW: dashboard logic (works without main.js)
│   ├── js/main.js            ← login/signup now call TB.auth.*
│   └── ...                   ← research/supervisors/publication/resources/about
│
├── sql/001_create_tables.sql ← paste this in the Supabase SQL Editor
├── sql/002_admin.sql         ← adds the is_admin flag (paste after 001)
├── scripts/seed_supabase.py  ← fills the content tables from seed/content.json
├── scripts/create_admin.py   ← creates the administrator account
├── seed/content.json         ← the exact sample content exported from js/data.js
│
├── requirements.txt          ← Python packages
├── .env.example              ← copy to .env and fill in your Supabase keys
├── vercel.json               ← Vercel function setting (maxDuration)
├── .python-version           ← tells Vercel to use Python 3.14
└── SETUP.md                  ← this file
```

### How a request travels (the short version)

```
Browser (public/index.html + js/api.js)
        │  fetch("/api/ideas")
        ▼
FastAPI route (app/routers/content.py)
        │  supabase-py client
        ▼
Supabase PostgreSQL (tables created by sql/001_create_tables.sql)
```

HTML pages and JavaScript are served as **static files** from `public/`.
Only URLs that start with `/api/` reach Python.

---

## 2. Create the Supabase project (once)

1. Go to <https://supabase.com> and sign in.
2. Click **New project**.
   - Name: `thesisbridge-bd`
   - Database password: choose a strong password and save it somewhere.
   - Region: **Southeast Asia (Singapore)** is the closest to Bangladesh.
3. Wait until the project status becomes **Active** (about 1–2 minutes).

### 2.1 Copy the three values

In the Supabase dashboard open **Project Settings → API** and copy:

| Value in the dashboard | Environment variable name | Used for |
| --- | --- | --- |
| Project URL | `SUPABASE_URL` | every Supabase call |
| `anon` / `public` key | `SUPABASE_ANON_KEY` | Supabase Auth calls (login/signup) |
| `service_role` key | `SUPABASE_SERVICE_ROLE_KEY` | table queries (server only) |

> ⚠️ **Never** put the `service_role` key in HTML or JavaScript. It can bypass
> the database's row-level security. It belongs only in `.env` and in Vercel's
> environment variables.

### 2.2 Create the tables

1. In the dashboard click **SQL Editor → New query**.
2. Open `sql/001_create_tables.sql` from this project, copy **all** of it,
   paste it into the editor and press **Run**.
3. You should see `Success. No rows returned`.

The file creates 16 tables in three groups:

| Group | Tables |
| --- | --- |
| Reference / filters | `categories`, `filter_options` |
| Public content | `research_ideas`, `supervisors`, `resources`, `publication_guides`, `roadmap_steps`, `faqs`, `journal_checklist_items` |
| User data | `profiles`, `idea_bookmarks`, `saved_supervisors`, `roadmap_progress`, `read_guides`, `checklist_progress`, `connection_requests` |

It also:

- adds indexes for the columns the API filters on,
- turns on **Row Level Security** and adds policies, so even if somebody used
  the public `anon` key directly, they could not read another student's rows,
- adds a trigger that keeps `profiles.updated_at` current.

The file can be run again safely: it uses `create table if not exists` and
drops each policy before recreating it.

### 2.3 Add the administrator flag

The dashboard needs one extra column on `profiles` that `001` does not have.

1. **SQL Editor → New query** again.
2. Open `sql/002_admin.sql`, copy all of it, paste and **Run**.
3. `Success. No rows returned` means the column and its index now exist.

The file only adds `profiles.is_admin boolean not null default false` and a
partial index on the rows where it is true. It changes no existing data.

### 2.4 Email confirmation

Sign-up in this project uses the Supabase **admin API** with
`email_confirm=True`, so a new account is usable immediately. You do **not**
have to configure an SMTP server for the demo.

(If you later want real confirmation emails: Authentication → Providers →
Email → enable *Confirm email*, and Sign-up uses the normal flow instead.)

---

## 3. Run everything locally

### 3.1 Open a terminal in the project folder

```powershell
cd "D:\web dev\thesisbridge-bd"
```

### 3.2 Create a virtual environment and install packages

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

`requirements.txt` contains exactly five things:

| Package | Why |
| --- | --- |
| `fastapi` | the web framework (routes, validation, `/docs`) |
| `uvicorn[standard]` | the server that runs FastAPI on your computer |
| `supabase` | official Python client for Supabase |
| `python-dotenv` | reads the `.env` file |
| `pydantic[email]` | data validation + email format checking |

### 3.3 Create your `.env` file

Copy the example file and fill in the three Supabase values:

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` should look like this (your values are different):

```ini
SUPABASE_URL=https://abcdefghijklm.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
CORS_ORIGINS=*
```

`CORS_ORIGINS=*` is fine for development. It means "any website may call this
API from a browser". The API still requires a valid token for private data.

### 3.4 Fill the database with content

```powershell
.\.venv\Scripts\python.exe scripts\seed_supabase.py
```

Expected output:

```
Reading ...\seed\content.json
Connecting to Supabase...
Seeding content tables...
  categories: 9 rows
  filter_options: 58 rows
  research_ideas: 20 rows
  supervisors: 12 rows
  resources: 20 rows
  publication_guides: 7 rows
  roadmap_steps: 8 rows
  faqs: 8 rows
  journal_checklist_items: 8 rows

Verification (row counts in Supabase):
  categories                 expected   9   found   9   OK
  ...
Done. Every content table is ready.
```

The script uses `upsert`, so running it twice does not create duplicates and
never touches user tables.

### 3.5 Create the administrator account

Once `.env` is filled in (step 3.3) and the flag exists (step 2.3):

```powershell
.\.venv\Scripts\python.exe scripts\create_admin.py --password "choose-a-strong-password"
```

Expected output:

```
  created auth user   admin@thesisbridge.bd
  profile flagged     is_admin = true

Administrator ready: admin@thesisbridge.bd
Password is stored hashed in Supabase Auth (not in any file).
Sign in at /admin.html
```

Why a script and not a password written in the code: the repository can be
read by anyone. This creates a **real Supabase Auth user** — the password
exists only as a bcrypt hash inside `auth.users`, exactly like a student's.
Running the same command again with a new `--password` changes it. The email
can be changed with `--email`.

### 3.6 Start the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open these two URLs:

- <http://127.0.0.1:8000/api/health> → should say `"databaseConfigured": true`
- <http://127.0.0.1:8000/docs> → interactive documentation; you can click
  **Try it out** on every endpoint (great for a live demo).

### 3.7 Start the website (second terminal)

```powershell
cd "D:\web dev\thesisbridge-bd"
python -m http.server 8417 --directory public
```

Open <http://127.0.0.1:8417/index.html>.

`js/api.js` automatically uses `http://127.0.0.1:8000` when the page runs on
localhost, so both servers must be running at the same time.

> If you open the HTML by double-clicking the file (`file://`), the API URL is
> still `http://127.0.0.1:8000`, but some browsers block `fetch` from `file://`.
> Using `http.server` above avoids that problem.

### 3.8 Test that it really works

1. Open the site → **Get Started** → create an account.
2. The navbar should greet you by your first name.
3. Save an idea (bookmark icon), complete a roadmap step, tick a checklist item.
4. In Supabase open **Table Editor** and look at `profiles`,
   `idea_bookmarks`, `roadmap_progress`, `checklist_progress` — your rows are
   there.
5. Log out, log in again, or open the site on another browser: the saved data
   comes back, because it is now in the database, not in the browser.
6. Open <http://127.0.0.1:8417/admin.html>, sign in with the administrator
   account, and check the four cards, the student table and the request inbox.
   Sign in with a **student** account instead and the page must answer
   "This account is not an administrator."

---

## 4. How the code is organised (for the viva)

### 4.1 Two Supabase clients — and why

`app/database.py` creates two clients and reuses them:

| Client | Key | Used by | Why this key |
| --- | --- | --- | --- |
| `get_auth_client()` | `anon` | `app/routers/auth.py`, `app/dependencies.py` | Auth endpoints are designed for the public key; we do not give them more power than needed. |
| `get_admin_client()` | `service_role` | content + user-state routes, seeder | Table reads/writes must bypass RLS, and RLS must only be bypassed on the server. |

Both are created lazily (only on first use) and stored in a module-level
variable, so a request does not pay the cost of creating a new client.

### 4.2 Login and sign-up

```
POST /api/auth/signup
  1. admin.auth.admin.create_user({ email, password, email_confirm: true })
     → Supabase hashes the password (bcrypt) and stores it in auth.users
  2. insert a row into public.profiles (name, university, department, ...)
  3. auth.sign_in_with_password(...) → returns an access token
  4. the browser stores only that token in localStorage

POST /api/auth/login
  1. auth.sign_in_with_password({ email, password })
  2. Supabase compares the bcrypt hash, returns user + access token
  3. backend loads (or repairs) the profile row and returns it

Any protected request
  Authorization: Bearer <token>
  → dependencies.get_current_user() calls auth.get_user(token)
  → 401 if the token is missing, expired or invalid
```

Passwords are **never** hashed or stored by our own Python code. Supabase Auth
owns that responsibility, which is safer than writing our own crypto.

### 4.3 camelCase vs snake_case

| Place | Style | Example |
| --- | --- | --- |
| PostgreSQL columns | `snake_case` | `supervisor_id`, `created_at` |
| API JSON | `camelCase` | `supervisorId`, `date` |
| JavaScript | `camelCase` | `request.supId` |

`app/schemas.py` uses `alias_generator=to_camel`, so Pydantic does the
translation automatically. `populate_by_name=True` lets Python code use the
snake_case names when creating a model.

### 4.4 How saved lists stay in sync

Every list (bookmarks, saved supervisors, roadmap steps, read guides,
checklist ticks) follows one simple rule:

```
localStorage is updated first  →  UI reacts instantly (optimistic update)
then the whole list is PUT to the API in the background
```

Because the whole list is sent, the endpoint is **idempotent**: sending the
same list twice gives the same result. `app/routers/user_state.py` first
`upsert`s the requested rows and only then deletes rows that are no longer in
the list, so a bad request cannot wipe the user's data.

Guests keep the old localStorage behaviour; the sync starts working the moment
they log in (the login response triggers `hydrate()` in `js/api.js`).

### 4.5 Connection requests

`POST /api/connection-requests` is public on purpose: the form can be used
before creating an account. When a logged-in user sends it, the backend also
stores their `user_id`, so the request appears in `GET /api/me/connection-requests`.
`js/api.js` compares the old and new arrays and sends only the difference
(POST for a new supervisor, DELETE when withdrawn).

### 4.6 How the administrator dashboard is protected

The rule is kept in **one place**, the database column `profiles.is_admin`:

```
request  ──►  get_current_user()      reads the Bearer token, asks Supabase
          ──►  require_admin()        SELECT is_admin FROM profiles WHERE id = user.id
          ──►  router                 runs only when that value is true
```

- No token → **401**. A real student → **403**. The column missing → **503**
  with the sentence "run sql/002_admin.sql", not a cryptic error.
- `admin.js` also checks `user.isAdmin` before drawing the dashboard, but that
  is only so a student sees a friendly message. Deleting that check would not
  open the data, because Python enforces the rule on every request.
- There are no extra RLS policies for the dashboard: the API already talks to
  Supabase with the **service-role key**, which bypasses RLS. Adding a second
  set of rules would mean two places to keep correct.
- `ProfileUpdate` (the schema students can send) has no `is_admin` field, so a
  student cannot promote themselves by editing their profile.

---

## 5. Deploy on Vercel

Vercel's FastAPI support serves **one Python function** and the static files
from `public/` on the same domain.

### 5.1 Put the project on GitHub

```powershell
cd "D:\web dev\thesisbridge-bd"
git init
git add .
git commit -m "Add FastAPI backend and Supabase integration"
git branch -M main
git remote add origin https://github.com/<your-username>/thesisbridge-bd.git
git push -u origin main
```

Before pushing, confirm `.gitignore` excludes `.env` and `.venv`. It does.

### 5.2 Import the repository in Vercel

1. Go to <https://vercel.com/new> and sign in with GitHub.
2. Choose the repository → **Import**.
3. **Root Directory**: leave empty (the repository root).
4. Vercel detects the Python/FastAPI project automatically from
   `requirements.txt` + `app/main.py`. Framework preset: **FastAPI**.
5. Do **not** set a build command. Vercel installs `requirements.txt` and
   builds the function itself.

### 5.3 Add the environment variables

Open **Settings → Environment Variables** and add these three (same values as
your `.env`), for **Production**, **Preview** and **Development**:

```
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
```

Optional, after the first deploy gives you a domain:

```
CORS_ORIGINS=https://your-project.vercel.app
```

Using `*` also works, because the API authenticates with a Bearer token rather
than cookies.

### 5.4 Deploy and check

Click **Deploy**. When it finishes, open:

| URL | Expected |
| --- | --- |
| `https://your-project.vercel.app/` | the website |
| `https://your-project.vercel.app/admin.html` | the administrator sign-in gate |
| `https://your-project.vercel.app/api/health` | `"databaseConfigured": true` |
| `https://your-project.vercel.app/docs` | API documentation (30 endpoints) |

Then create an account on the live site and confirm the row appears in the
Supabase `profiles` table. The administrator account is created once from your
computer with `scripts/create_admin.py` (step 3.5); it works on the live site
immediately because it is a normal Supabase Auth user.

### 5.5 What makes Vercel work here

| File / folder | Role on Vercel |
| --- | --- |
| `app/main.py` | Vercel looks for a `FastAPI` object named `app` at this entrypoint. |
| `public/` | Vercel serves this folder at `/` (HTML, CSS, JS, images). |
| `requirements.txt` | Vercel installs these packages before building the function. |
| `.python-version` | pins Python 3.14. |
| `vercel.json` | pins the framework to `fastapi` and gives the function `maxDuration: 30` seconds (Supabase calls can be slow). |

`js/api.js` uses a **relative** URL in production (`"" + "/api/content"`), so
the same code works locally and on Vercel without any change.

---

## 6. API reference

Public (no token needed):

| Method | Path | What it returns |
| --- | --- | --- |
| GET | `/api/health` | service status + whether keys are configured |
| GET | `/api/content` | everything (ideas, supervisors, resources, guides, ...) in one call |
| GET | `/api/ideas?q=&category=&difficulty=&type=&technology=&sort=&limit=&offset=` | paginated ideas |
| GET | `/api/ideas/{id}` | one idea |
| GET | `/api/supervisors?q=&university=&department=&area=&expertise=` | paginated supervisors |
| GET | `/api/supervisors/{id}` | one supervisor |
| GET | `/api/resources?q=&category=` | paginated resources |
| GET | `/api/resources/{id}` | one resource |
| GET | `/api/publication-guides` | the 7 publication guides |
| GET | `/api/publication-guides/{slug}` | one guide |
| GET | `/api/roadmap` | the 8 roadmap steps |
| GET | `/api/faqs` | the 8 FAQs |
| GET | `/api/checklist` | the 8 checklist items |
| POST | `/api/auth/signup` | create account (name, email, password, ...) |
| POST | `/api/auth/login` | log in (email, password) |
| POST | `/api/connection-requests` | send a supervisor request (works for guests too) |

Needs `Authorization: Bearer <token>`:

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/auth/me` | current user's profile |
| GET | `/api/me/state` | profile + every saved list + connection requests |
| PUT | `/api/me/bookmarks/ideas` | replace saved idea ids |
| PUT | `/api/me/bookmarks/supervisors` | replace saved supervisor ids |
| PUT | `/api/me/roadmap` | replace completed step ids |
| PUT | `/api/me/read-guides` | replace read guide ids |
| PUT | `/api/me/checklist` | replace checklist item ids |
| PUT | `/api/me/profile` | update name / university / department / student id / interest |
| GET | `/api/me/connection-requests` | my requests |
| DELETE | `/api/me/connection-requests/{supervisor_id}` | withdraw one request |

Needs `Authorization: Bearer <token>` **and** `profiles.is_admin = true`:

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/admin/overview` | counts + most-bookmarked ideas |
| GET | `/api/admin/students` | every student with activity counts |
| GET | `/api/admin/connection-requests?status=` | inbox, optionally filtered by `pending` / `accepted` / `declined` |
| PUT | `/api/admin/connection-requests/{id}/status` | set a request to `pending`, `accepted` or `declined` |

Errors use normal HTTP status codes and a `detail` message:

| Code | Meaning in this project |
| --- | --- |
| 400 | one of the ids you sent does not exist |
| 401 | missing / expired token, or wrong email + password |
| 403 | a valid token, but that account is not an administrator |
| 404 | record not found |
| 409 | that email already has an account |
| 422 | a field is missing or invalid (FastAPI validation) |
| 503 | `.env` / Vercel environment variables are not filled in |

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `/api/health` shows `"databaseConfigured": false` | `.env` missing or empty | fill the three values, restart uvicorn |
| `/api/content` returns 503 | same as above | same as above |
| `Could not read the categories table` in the seeder | SQL file not run, or wrong keys | run `sql/001_create_tables.sql` in the SQL Editor |
| Login always says "Incorrect email or password" | account was created with an unconfirmed email outside this app | re-create it through the site's sign-up form |
| Website still shows old content | backend not running, browser cached JS | check `http://127.0.0.1:8000/api/health`, hard-refresh with Ctrl+F5 |
| CORS error in the browser console | API not running, or `CORS_ORIGINS` does not include the page origin | start uvicorn; set `CORS_ORIGINS=*` locally |
| Vercel returns 500 | environment variables missing in Vercel | Settings → Environment Variables, then redeploy |
| Supabase project paused | free plan pauses after ~7 days idle | open the dashboard and restore the project |

---

## 8. Known limitations (be honest in the presentation)

1. **Access tokens last one hour.** There is no refresh-token rotation in the
   frontend; after an hour the user is asked to log in again. Supabase supports
   refresh tokens — this was left out to keep the code short and explainable.
2. **Connection requests are stored, not emailed.** There is no SMTP service in
   this project, so the supervisor's email address is shown in the form.
3. **The matching quiz still runs in the browser.** It is a scoring formula
   over the supervisor data, and the UI labels it as a demo recommendation.
4. **The administrator dashboard can read and triage, not edit.** It shows every
   student and lets you set a connection request to accepted or declined, but
   changing ideas, supervisors or guides still means SQL or the seeder.
5. **Supabase's free plan** pauses inactive projects and has storage limits.
