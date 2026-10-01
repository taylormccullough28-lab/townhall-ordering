-- One GroupMe bot per store.
--
-- RLS is on with NO policies, deliberately. A bot_id is a bearer token: anyone
-- holding it can post to that group indefinitely with no further auth. With no
-- policy, anon and authenticated roles cannot read this table at all. Only the
-- service role bypasses RLS, and that key lives in the edge function's
-- environment and never reaches a browser.

create table public.preshift_bots (
  store      text primary key,
  bot_id     text not null,
  label      text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.preshift_bots enable row level security;

comment on table public.preshift_bots is
  'One GroupMe bot per store. Read only by the preshift-post edge function using the service role key. Never expose bot_id to a browser.';

comment on column public.preshift_bots.store is
  'Store key the board sends, e.g. townhall-columbus. The test group uses "test".';

-- pg_net is enabled in this project so the relay can be exercised from SQL
-- without a browser. Not required by the function itself.
create extension if not exists pg_net;
