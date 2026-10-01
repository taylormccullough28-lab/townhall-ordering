-- v1 foundation: stores, roster, boards, 86 list, and the permission layer.
-- Field shapes follow the prototype so the UI ports mechanically.

create type public.app_role as enum ('manager', 'gm', 'admin');

create table public.stores (
  id         text primary key,                      -- 'townhall-columbus'
  name       text not null,
  concept    text,
  created_at timestamptz not null default now()
);

-- The roster. Managers sign in with personal email against this list, because
-- they have no company directory - so this table IS access control, and
-- removing someone here is what revokes them. user_id is null until their
-- first magic-link sign-in binds an auth user to the row.
create table public.managers (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid unique references auth.users(id) on delete set null,
  email           text not null,
  full_name       text,
  role            public.app_role not null default 'manager',
  active          boolean not null default true,
  created_at      timestamptz not null default now(),
  deactivated_at  timestamptz
);

create unique index managers_email_lower_idx on public.managers (lower(email));

comment on table public.managers is
  'The roster Taylor controls. Setting active=false is what removes a departed manager''s access; there is no directory to do it automatically.';

create table public.manager_stores (
  manager_id uuid not null references public.managers(id) on delete cascade,
  store_id   text not null references public.stores(id) on delete cascade,
  primary key (manager_id, store_id)
);

-- One board per store per date per shift.
--
-- coaching is a SEPARATE column from content on purpose. The decision is that
-- coaching notes are visible on their own shift and never resurface. Keeping
-- them out of the general content blob makes that rule enforceable at the data
-- layer instead of trusting every future screen to remember it.
create table public.boards (
  id         uuid primary key default gen_random_uuid(),
  store_id   text not null references public.stores(id),
  board_date date not null,
  shift      text not null check (shift in ('am', 'pm')),
  content    jsonb not null default '{}'::jsonb,
  coaching   jsonb not null default '{}'::jsonb,
  posted_at  timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (store_id, board_date, shift)
);

comment on column public.boards.coaching is
  'Day-of only. Never surfaced on any later date, report or carry-forward. Separate from content so the rule is structural.';

-- The 86 list is its own table rather than JSON inside content. The PRD's
-- sharpest success measure is "86 items added mid-shift", which needs a real
-- timestamp per item, and every item carries its own attribution and
-- lifecycle. Both are painful inside a blob.
create table public.eighty_six (
  id         uuid primary key default gen_random_uuid(),
  board_id   uuid not null references public.boards(id) on delete cascade,
  item       text not null,
  status     text not null default '86' check (status in ('86', 'low', 'back')),
  note       text not null default '',
  added_by   uuid references public.managers(id),
  added_at   timestamptz not null default now(),
  changed_by uuid references public.managers(id),
  changed_at timestamptz
);

create index eighty_six_board_idx on public.eighty_six (board_id, added_at);

-- Helpers are SECURITY DEFINER so they bypass RLS and cannot recurse through
-- the policies that call them.
create or replace function public.current_manager_id() returns uuid
  language sql stable security definer set search_path = public as $$
  select m.id from public.managers m where m.user_id = auth.uid() and m.active
$$;

create or replace function public.current_role() returns public.app_role
  language sql stable security definer set search_path = public as $$
  select m.role from public.managers m where m.user_id = auth.uid() and m.active
$$;

create or replace function public.sees_all_stores() returns boolean
  language sql stable security definer set search_path = public as $$
  select coalesce(public.current_role() in ('gm', 'admin'), false)
$$;

create or replace function public.can_see_store(target text) returns boolean
  language sql stable security definer set search_path = public as $$
  select public.sees_all_stores() or exists (
    select 1 from public.manager_stores ms
    where ms.store_id = target and ms.manager_id = public.current_manager_id()
  )
$$;

alter table public.stores          enable row level security;
alter table public.managers        enable row level security;
alter table public.manager_stores  enable row level security;
alter table public.boards          enable row level security;
alter table public.eighty_six      enable row level security;

-- Stores: anyone on the roster reads; only admin writes.
create policy stores_read on public.stores for select
  using (public.current_manager_id() is not null);
create policy stores_admin_write on public.stores for all
  using (public.current_role() = 'admin') with check (public.current_role() = 'admin');

-- Managers: you see yourself; GM and admin see the roster; only admin edits it.
create policy managers_read_self on public.managers for select
  using (user_id = auth.uid() or public.sees_all_stores());
create policy managers_admin_write on public.managers for all
  using (public.current_role() = 'admin') with check (public.current_role() = 'admin');

create policy manager_stores_read on public.manager_stores for select
  using (manager_id = public.current_manager_id() or public.sees_all_stores());
create policy manager_stores_admin_write on public.manager_stores for all
  using (public.current_role() = 'admin') with check (public.current_role() = 'admin');

-- Boards: scoped to the stores you are assigned to. Enforced here, not in the app.
create policy boards_read on public.boards for select
  using (public.can_see_store(store_id));
create policy boards_write on public.boards for all
  using (public.can_see_store(store_id)) with check (public.can_see_store(store_id));

create policy eighty_six_read on public.eighty_six for select
  using (exists (select 1 from public.boards b
                 where b.id = board_id and public.can_see_store(b.store_id)));
create policy eighty_six_write on public.eighty_six for all
  using (exists (select 1 from public.boards b
                 where b.id = board_id and public.can_see_store(b.store_id)))
  with check (exists (select 1 from public.boards b
                      where b.id = board_id and public.can_see_store(b.store_id)));
