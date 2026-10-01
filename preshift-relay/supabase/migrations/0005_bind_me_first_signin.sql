-- First sign-in binds an auth user to their roster row. This cannot be done by
-- the client: the managers policies gate writes on current_role() = 'admin',
-- and current_role() resolves through user_id = auth.uid(), which is null until
-- the binding exists. Binding required already being bound.
--
-- SECURITY DEFINER to bypass that, with the dangerous part removed: the email
-- is read from the VERIFIED JWT claim, never passed in. A caller cannot name a
-- row to claim, so they cannot bind themselves to somebody else's. Only an
-- unbound, active row matching their own verified address is ever touched.
create or replace function public.bind_me()
returns public.managers
language plpgsql
security definer
set search_path = public
as $$
declare
  claim_email text;
  found_row   public.managers;
begin
  if auth.uid() is null then
    return null;
  end if;

  select * into found_row from public.managers where user_id = auth.uid();
  if found then
    return found_row;
  end if;

  claim_email := lower(nullif(trim(coalesce(auth.jwt() ->> 'email', '')), ''));
  if claim_email is null then
    return null;
  end if;

  update public.managers
     set user_id = auth.uid()
   where lower(email) = claim_email
     and user_id is null
     and active
  returning * into found_row;

  return found_row;
end;
$$;

revoke all on function public.bind_me() from public;
grant execute on function public.bind_me() to authenticated;

comment on function public.bind_me() is
  'First-sign-in binding. Reads the address from the verified JWT, never an argument, so a caller cannot claim another person''s roster row. Idempotent.';
