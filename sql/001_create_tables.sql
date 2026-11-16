-- ============================================================================
-- ThesisBridge BD - Supabase / PostgreSQL schema
-- ============================================================================
-- HOW TO USE THIS FILE
--   1. Open your Supabase project dashboard.
--   2. Click "SQL Editor" -> "New query".
--   3. Paste this whole file and press "Run".
--   4. Then run:  python scripts/seed_supabase.py   (fills the content tables)
--
-- The file is safe to run more than once: tables use IF NOT EXISTS and every
-- policy is dropped before it is created again.
-- ============================================================================

-- pgcrypto gives us gen_random_uuid() for UUID primary keys.
create extension if not exists pgcrypto;


-- ============================================================================
-- 1. REFERENCE TABLES (small vocabularies used by the website filters)
-- ============================================================================

-- Research categories shown in the filter chips, e.g. "Artificial Intelligence".
-- "position" keeps the exact order used by the frontend.
create table if not exists public.categories (
  name      text primary key,
  short     text,
  icon      text not null,
  position  integer not null default 0
);

-- One generic table for every simple filter list. Instead of creating seven
-- tiny tables we store a "kind" column:
--   difficulty | type | technology | quiz_technology | university
--   | department | expertise
create table if not exists public.filter_options (
  id        bigserial primary key,
  kind      text not null,
  value     text not null,
  position  integer not null default 0,
  unique (kind, value)
);


-- ============================================================================
-- 2. CONTENT TABLES (public reading data, seeded from js/data.js)
-- ============================================================================

-- The 20 research idea cards. Arrays use PostgreSQL's text[] type and the
-- nested lists (actions, sections...) use jsonb where the shape varies.
create table if not exists public.research_ideas (
  id             integer primary key,
  title          text not null,
  description    text not null,
  category       text not null references public.categories(name),
  area           text not null,
  difficulty     text not null,
  technologies   text[] not null default '{}',
  type           text not null,
  universities   text[] not null default '{}',
  tags           text[] not null default '{}',
  problem        text not null,
  gap            text not null,
  methodology    text not null,
  outcome        text not null,
  keywords       text[] not null default '{}',
  featured       integer not null default 0,
  created_at     timestamptz not null default now()
);

-- The 12 supervisor profiles.
create table if not exists public.supervisors (
  id                 integer primary key,
  name               text not null,
  title              text not null,
  university         text not null,
  department         text not null,
  interests          text[] not null default '{}',
  expertise          text[] not null default '{}',
  areas              text[] not null default '{}',
  publications       integer not null default 0,
  supervision_types  text[] not null default '{}',
  accepting          boolean not null default false,
  email              text not null,
  office             text not null,
  bio                text not null,
  selected_pubs      text[] not null default '{}',
  supervision_areas  text[] not null default '{}',
  suggested_topics   text[] not null default '{}'
);

-- The 20 learning resources.
create table if not exists public.resources (
  id           integer primary key,
  title        text not null,
  category     text not null,
  type         text not null,
  type_icon    text not null,
  level        text not null,
  minutes      integer not null default 0,
  description  text not null,
  details      text not null,
  learn_points text[] not null default '{}',
  url          text,
  tags         text[] not null default '{}'
);

-- The 7 Publication Hub guides. Their id is a readable slug such as
-- "journal-selection", which the frontend uses as the localStorage key.
create table if not exists public.publication_guides (
  id        text primary key,
  icon      text not null,
  title     text not null,
  summary   text not null,
  sections  jsonb not null default '[]',
  tips      text[] not null default '{}',
  position  integer not null default 0
);

-- The 8 research roadmap steps.
create table if not exists public.roadmap_steps (
  id           integer primary key,
  icon         text not null,
  title        text not null,
  explanation  text not null,
  actions      text[] not null default '{}',
  resources    jsonb not null default '[]'
);

-- The 8 frequently asked questions.
create table if not exists public.faqs (
  id       integer primary key,
  question text not null,
  answer   text not null
);

-- The 8 items of the journal submission checklist.
create table if not exists public.journal_checklist_items (
  id        text primary key,
  label     text not null,
  position  integer not null default 0
);


-- ============================================================================
-- 3. USER TABLES (Supabase Auth keeps email + password; we keep the profile)
-- ============================================================================

-- Supabase stores real authentication data in the hidden "auth.users" table.
-- This public table stores everything a user types in the sign-up form.
-- The primary key points at auth.users, so deleting an auth user also deletes
-- the profile (ON DELETE CASCADE).
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  name        text not null,
  email       text not null,
  university  text,
  department  text,
  student_id  text,
  interest    text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Ideas the user bookmarked. One row per (user, idea) pair; the composite
-- primary key makes duplicates impossible.
create table if not exists public.idea_bookmarks (
  user_id    uuid not null references auth.users(id) on delete cascade,
  idea_id    integer not null references public.research_ideas(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, idea_id)
);

-- Supervisors the user saved.
create table if not exists public.saved_supervisors (
  user_id       uuid not null references auth.users(id) on delete cascade,
  supervisor_id integer not null references public.supervisors(id) on delete cascade,
  created_at    timestamptz not null default now(),
  primary key (user_id, supervisor_id)
);

-- Roadmap steps the user marked as complete.
create table if not exists public.roadmap_progress (
  user_id    uuid not null references auth.users(id) on delete cascade,
  step_id    integer not null references public.roadmap_steps(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, step_id)
);

-- Publication guides the user already opened ("Read" badge).
create table if not exists public.read_guides (
  user_id    uuid not null references auth.users(id) on delete cascade,
  guide_id   text not null references public.publication_guides(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, guide_id)
);

-- Journal checklist ticks.
create table if not exists public.checklist_progress (
  user_id    uuid not null references auth.users(id) on delete cascade,
  item_id    text not null references public.journal_checklist_items(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, item_id)
);

-- Messages a student sends to a supervisor. user_id is nullable because the
-- website lets visitors send a request before creating an account.
create table if not exists public.connection_requests (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users(id) on delete set null,
  supervisor_id integer not null references public.supervisors(id) on delete cascade,
  name          text not null,
  email         text not null,
  topic         text not null,
  message       text not null,
  status        text not null default 'pending',
  created_at    timestamptz not null default now(),
  unique (user_id, supervisor_id)
);


-- ============================================================================
-- 4. INDEXES (speed up the queries the API makes most often)
-- ============================================================================

create index if not exists research_ideas_category_idx   on public.research_ideas (category);
create index if not exists research_ideas_difficulty_idx on public.research_ideas (difficulty);
create index if not exists research_ideas_type_idx       on public.research_ideas (type);
create index if not exists supervisors_university_idx    on public.supervisors (university);
create index if not exists connection_requests_user_idx  on public.connection_requests (user_id);


-- ============================================================================
-- 5. ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- RLS is PostgreSQL's built-in permission system. When it is ON, nobody can
-- read a row unless a policy allows it.
--
-- IMPORTANT: the Python backend uses the SERVICE ROLE key, and a service role
-- key bypasses RLS completely. RLS still matters because it protects the
-- database if somebody ever talks to Supabase directly with the public anon
-- key. Never put the service role key in the browser!
-- ============================================================================

-- ---- 5a. Public content: readable by anyone, writable only by server ------

alter table public.categories               enable row level security;
alter table public.filter_options           enable row level security;
alter table public.research_ideas           enable row level security;
alter table public.supervisors              enable row level security;
alter table public.resources                enable row level security;
alter table public.publication_guides       enable row level security;
alter table public.roadmap_steps            enable row level security;
alter table public.faqs                     enable row level security;
alter table public.journal_checklist_items  enable row level security;

drop policy if exists "Public content is readable" on public.categories;
create policy "Public content is readable" on public.categories
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.filter_options;
create policy "Public content is readable" on public.filter_options
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.research_ideas;
create policy "Public content is readable" on public.research_ideas
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.supervisors;
create policy "Public content is readable" on public.supervisors
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.resources;
create policy "Public content is readable" on public.resources
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.publication_guides;
create policy "Public content is readable" on public.publication_guides
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.roadmap_steps;
create policy "Public content is readable" on public.roadmap_steps
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.faqs;
create policy "Public content is readable" on public.faqs
  for select to anon, authenticated using (true);

drop policy if exists "Public content is readable" on public.journal_checklist_items;
create policy "Public content is readable" on public.journal_checklist_items
  for select to anon, authenticated using (true);


-- ---- 5b. Profiles: a user may only see and edit their own profile ----------

alter table public.profiles enable row level security;

drop policy if exists "Users read their own profile" on public.profiles;
create policy "Users read their own profile" on public.profiles
  for select to authenticated using (auth.uid() = id);

drop policy if exists "Users update their own profile" on public.profiles;
create policy "Users update their own profile" on public.profiles
  for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);


-- ---- 5c. Personal lists: each user owns their rows -------------------------
-- The pattern is the same for all five tables, so it is easy to remember:
--   auth.uid() = user_id

alter table public.idea_bookmarks     enable row level security;
alter table public.saved_supervisors  enable row level security;
alter table public.roadmap_progress   enable row level security;
alter table public.read_guides        enable row level security;
alter table public.checklist_progress enable row level security;

drop policy if exists "Users manage their own idea bookmarks" on public.idea_bookmarks;
create policy "Users manage their own idea bookmarks" on public.idea_bookmarks
  for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users manage their own saved supervisors" on public.saved_supervisors;
create policy "Users manage their own saved supervisors" on public.saved_supervisors
  for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users manage their own roadmap progress" on public.roadmap_progress;
create policy "Users manage their own roadmap progress" on public.roadmap_progress
  for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users manage their own read guides" on public.read_guides;
create policy "Users manage their own read guides" on public.read_guides
  for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users manage their own checklist progress" on public.checklist_progress;
create policy "Users manage their own checklist progress" on public.checklist_progress
  for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);


-- ---- 5d. Connection requests ----------------------------------------------

alter table public.connection_requests enable row level security;

-- A logged-in student can read the requests they sent.
drop policy if exists "Users read their own connection requests" on public.connection_requests;
create policy "Users read their own connection requests" on public.connection_requests
  for select to authenticated using (auth.uid() = user_id);

-- A logged-in student can withdraw (delete) their own request.
drop policy if exists "Users delete their own connection requests" on public.connection_requests;
create policy "Users delete their own connection requests" on public.connection_requests
  for delete to authenticated using (auth.uid() = user_id);

-- Anonymous visitors cannot insert directly through Supabase; the Python
-- backend inserts guest requests with the service role key instead.


-- ============================================================================
-- 6. HELPER FUNCTION: keep profiles.updated_at fresh
-- ============================================================================

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_touch_updated_at on public.profiles;
create trigger profiles_touch_updated_at
  before update on public.profiles
  for each row execute function public.touch_updated_at();
