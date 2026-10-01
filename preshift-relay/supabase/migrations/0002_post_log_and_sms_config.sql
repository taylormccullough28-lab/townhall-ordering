-- Every successful post, one row. This is the completion history the PRD asks
-- for: "logged by the relay when the post is sent". Written server-side, so a
-- client cannot fabricate a completion it did not send.
create table public.post_log (
  id           bigserial primary key,
  store        text not null,
  sent_at      timestamptz not null default now(),
  chars        integer not null,
  parts        integer not null,
  notified     boolean not null default false,
  notify_error text
);

create index post_log_store_sent_at_idx on public.post_log (store, sent_at desc);

alter table public.post_log enable row level security;

comment on table public.post_log is
  'One row per successful GroupMe post. Completion history. Written only by the preshift-post edge function.';
comment on column public.post_log.notify_error is
  'Why the completion text did not send, if it did not. A failed text never fails the post - the post already went out.';

-- Twilio credentials for the completion text. Deliberately empty: the values go
-- in through the Supabase dashboard, not through a chat window, for the same
-- reason the GroupMe bot token does not live in the board.
--
-- Toll-free number, not 10-digit. A 10-digit number would require A2P 10DLC
-- brand and campaign registration, and since 2026-06-30 a privacy policy and
-- terms URL on every campaign - disproportionate for texting one person.
create table public.sms_config (
  id          integer primary key default 1 check (id = 1),
  account_sid text,
  auth_token  text,
  from_number text,
  to_number   text,
  enabled     boolean not null default false,
  updated_at  timestamptz not null default now()
);

alter table public.sms_config enable row level security;

insert into public.sms_config (id) values (1);

comment on table public.sms_config is
  'Single row. Twilio credentials for the completion text, read only by the preshift-post edge function via the service role. Set enabled once the toll-free number is verified.';
