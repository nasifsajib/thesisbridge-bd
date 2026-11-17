-- ============================================================================
-- ThesisBridge BD — 002_admin.sql
-- Adds the administrator flag used by the admin dashboard.
--
-- Run this ONCE in the Supabase dashboard:  SQL Editor -> New query -> paste
-- this whole file -> Run. It is safe to run twice (every statement checks
-- itself with "if not exists"), so a second run does nothing.
--
-- Why a column and not a config file?
--   Authorisation belongs with the data. The flag lives next to the user it
--   describes, it can be inspected in the table editor, and the backend reads
--   it on every admin request. A list of emails in an environment variable
--   would be invisible in the database and easy to get out of sync.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. The flag itself
-- ----------------------------------------------------------------------------
-- "not null default false" means every existing row becomes a normal student
-- automatically, and any future row is a student unless we say otherwise.
-- Only the service-role key can change it: profiles has no UPDATE policy for
-- the anon or authenticated roles, so a browser cannot promote itself.

alter table public.profiles
  add column if not exists is_admin boolean not null default false;


-- ----------------------------------------------------------------------------
-- 2. A small index
-- ----------------------------------------------------------------------------
-- Partial index: only the (very few) administrator rows are stored, so it
-- costs almost nothing and makes "find the admins" instant.

create index if not exists profiles_is_admin_idx
  on public.profiles (id)
  where is_admin;


-- ----------------------------------------------------------------------------
-- 3. Optional: promote your own existing account
-- ----------------------------------------------------------------------------
-- Uncomment the next line and replace the email if you would rather use a
-- normal account you already registered instead of the dedicated admin
-- account created by scripts/create_admin.py.
--
-- update public.profiles set is_admin = true where email = 'you@example.com';


-- ----------------------------------------------------------------------------
-- 4. Verify (this is what the SELECT at the end of a Run shows you)
-- ----------------------------------------------------------------------------
-- Expect the column to exist, and either 0 rows (before the admin account is
-- created) or 1 row for admin@thesisbridge.bd (afterwards).

select id, email, name, is_admin, created_at
from public.profiles
order by is_admin desc, created_at;
