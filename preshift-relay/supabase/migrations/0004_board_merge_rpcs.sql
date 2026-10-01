-- Deep merge, not `||`.
--
-- A shallow concatenation replaces whole sub-objects: one manager ticking
-- huddle1.server while another ticks huddle1.host would have the second write
-- wipe the first, because each sends {"huddle1": {...}}. Merging key by key
-- means two managers editing different cells of the same grid both survive.
create or replace function public.jsonb_deep_merge(a jsonb, b jsonb)
returns jsonb
language plpgsql immutable as $$
declare
  result jsonb;
  k      text;
begin
  if a is null then return b; end if;
  if b is null then return a; end if;
  if jsonb_typeof(a) <> 'object' or jsonb_typeof(b) <> 'object' then
    return b;   -- scalars and arrays: last writer wins
  end if;

  result := a;
  for k in select jsonb_object_keys(b) loop
    if a ? k then
      result := jsonb_set(result, array[k], public.jsonb_deep_merge(a -> k, b -> k));
    else
      result := jsonb_set(result, array[k], b -> k, true);
    end if;
  end loop;
  return result;
end;
$$;

-- SECURITY INVOKER on purpose: these run as the caller, so the boards policies
-- decide whether this manager may touch this store's board. A definer function
-- here would quietly bypass the permission layer.
create or replace function public.merge_board_content(target uuid, patch jsonb)
returns public.boards
language sql volatile security invoker set search_path = public as $$
  update public.boards
     set content    = public.jsonb_deep_merge(content, patch),
         updated_at = now()
   where id = target
  returning *;
$$;

create or replace function public.merge_board_coaching(target uuid, patch jsonb)
returns public.boards
language sql volatile security invoker set search_path = public as $$
  update public.boards
     set coaching   = public.jsonb_deep_merge(coaching, patch),
         updated_at = now()
   where id = target
  returning *;
$$;

-- Realtime needs the tables in the publication to emit postgres_changes.
alter publication supabase_realtime add table public.boards;
alter publication supabase_realtime add table public.eighty_six;
