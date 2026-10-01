/* Data layer for the pre-shift board.
 *
 * Replaces the prototype's two artifact capabilities:
 *   claude.use("db")   -> Supabase Postgres + realtime
 *   claude.use("user") -> Supabase Auth + the managers roster
 *
 * Deliberately a real API rather than a shim imitating the artifact one. A fake
 * Firestore-ish surface over Supabase would read as a mystery to whoever picks
 * this up next.
 *
 * Nothing here enforces access. Every table has RLS on and the policies live in
 * migration 0003; this file cannot grant itself more than the signed-in manager
 * already has. A dropped check here is a bug, not a security hole.
 */

const SUPABASE_URL = "https://mbbnzzvqkcqjfhonwalb.supabase.co";
// Publishable key. Public by design - it identifies the project, it does not
// authorise anything. Row access is decided by the signed-in user's JWT + RLS.
const SUPABASE_KEY = "sb_publishable_GyeS8YntNpZE2npl7vaVrw_O1COcRYL";

const RELAY_URL = SUPABASE_URL + "/functions/v1/preshift-post";

/* global supabase */
const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
});

let _manager = null; // the managers row for the signed-in user, or null

/* ---------------- auth ---------------- */

export const auth = {
  // Magic link. No passwords to reset for a manager at 4pm on a Friday.
  async signIn(email) {
    const { error } = await sb.auth.signInWithOtp({
      email: String(email || "").trim(),
      options: { emailRedirectTo: window.location.origin + window.location.pathname },
    });
    if (error) throw error;
  },

  async signOut() {
    _manager = null;
    await sb.auth.signOut();
  },

  // Resolves the managers row for the signed-in user, or null.
  //
  // First sign-in binds the auth user to their roster row by email. The roster
  // is the access list: an email that is not on it, or whose row is inactive,
  // resolves null here AND sees nothing through RLS. Both have to be true -
  // this one is for the UI, the RLS one is the actual control.
  async manager() {
    if (_manager) return _manager;
    const { data: { user } } = await sb.auth.getUser();
    if (!user) return null;

    // bind_me() resolves the roster row and, on a first sign-in, binds it.
    //
    // This has to run server-side. The earlier version did the UPDATE from here
    // and could never have worked: the managers policies gate writes on
    // current_role() = 'admin', and current_role() resolves through
    // user_id = auth.uid(), which is null until the binding exists. Binding
    // required already being bound.
    //
    // bind_me is SECURITY DEFINER so it bypasses that, and takes the address
    // from the verified JWT rather than an argument, so a caller cannot name a
    // row to claim. It is idempotent - safe to call on every page load.
    const { data, error } = await sb.rpc("bind_me");
    if (error) throw error;

    const row = Array.isArray(data) ? data[0] : data;
    _manager = row && row.active ? row : null;
    return _manager;
  },

  onChange(cb) {
    const { data } = sb.auth.onAuthStateChange(() => { _manager = null; cb(); });
    return () => data.subscription.unsubscribe();
  },
};

/* ---------------- stores ---------------- */

export const stores = {
  async list() {
    const { data, error } = await sb.from("stores").select("id, name, concept").order("name");
    if (error) throw error;
    return data || [];
  },
};

/* ---------------- boards ---------------- */

// One row per store + date + shift. `content` holds goal, events, notes and the
// position grids; `coaching` is separate because those notes are day-of only.
export const boards = {
  async load(storeId, date, shift) {
    const { data, error } = await sb
      .from("boards").select("*")
      .eq("store_id", storeId).eq("board_date", date).eq("shift", shift)
      .maybeSingle();
    if (error) throw error;
    return data;
  },

  // Creates on first write so an unopened shift leaves no empty row behind.
  async ensure(storeId, date, shift) {
    const existing = await boards.load(storeId, date, shift);
    if (existing) return existing;
    const { data, error } = await sb
      .from("boards").insert({ store_id: storeId, board_date: date, shift })
      .select().single();
    if (error) throw error;
    return data;
  },

  async patchContent(boardId, patch) {
    const { data, error } = await sb.rpc("merge_board_content", {
      target: boardId, patch,
    });
    if (error) throw error;
    return data;
  },

  async patchCoaching(boardId, patch) {
    const { data, error } = await sb.rpc("merge_board_coaching", {
      target: boardId, patch,
    });
    if (error) throw error;
    return data;
  },

  // Live sync, replacing the prototype's onSnapshot. One channel per board.
  subscribe(boardId, cb) {
    const ch = sb.channel("board:" + boardId)
      .on("postgres_changes",
          { event: "*", schema: "public", table: "boards", filter: "id=eq." + boardId },
          (p) => cb(p.new))
      .subscribe();
    return () => sb.removeChannel(ch);
  },
};

/* ---------------- the 86 list ---------------- */

// Its own table, so each item carries a real timestamp and its own attribution.
export const eightySix = {
  async list(boardId) {
    const { data, error } = await sb
      .from("eighty_six").select("*").eq("board_id", boardId).order("added_at");
    if (error) throw error;
    return data || [];
  },

  async add(boardId, item, note) {
    const m = await auth.manager();
    const { data, error } = await sb.from("eighty_six")
      .insert({ board_id: boardId, item, note: note || "", added_by: m ? m.id : null })
      .select().single();
    if (error) throw error;
    return data;
  },

  async update(id, patch) {
    const m = await auth.manager();
    const { data, error } = await sb.from("eighty_six")
      .update({ ...patch, changed_by: m ? m.id : null, changed_at: new Date().toISOString() })
      .eq("id", id).select().single();
    if (error) throw error;
    return data;
  },

  subscribe(boardId, cb) {
    const ch = sb.channel("86:" + boardId)
      .on("postgres_changes",
          { event: "*", schema: "public", table: "eighty_six",
            filter: "board_id=eq." + boardId },
          () => cb())
      .subscribe();
    return () => sb.removeChannel(ch);
  },
};

/* ---------------- names, for attribution ---------------- */

export const people = {
  // Resolve ids to names at render time, never stored alongside the record.
  async names(managerIds) {
    const ids = [...new Set((managerIds || []).filter(Boolean))];
    if (!ids.length) return {};
    const { data } = await sb.from("managers").select("id, full_name").in("id", ids);
    const out = {};
    for (const r of data || []) out[r.id] = r.full_name || "";
    return out;
  },
};

/* ---------------- posting ---------------- */

// The relay holds the GroupMe bot token; this only sends text. A plain fetch,
// which is exactly what the artifact prototype could not do.
export const post = {
  async send(storeId, text) {
    const r = await fetch(RELAY_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: SUPABASE_KEY,
        Authorization: "Bearer " + SUPABASE_KEY,
      },
      body: JSON.stringify({ store: storeId, text }),
    });
    const body = await r.json().catch(() => null);
    if (!r.ok || !body || !body.ok) {
      throw new Error((body && body.error) || "post failed (HTTP " + r.status + ")");
    }
    return body; // { ok, messages, logged, notified, notifyNote }
  },
};

/* ---------------- the roster ---------------- */

/* Admin only, enforced by the managers_admin_write policy rather than by hiding
 * buttons. A non-admin calling any of these gets a refused write from Postgres,
 * which is the point: the screen is a convenience, not the control.
 *
 * Rows are deactivated, never deleted. Deleting one would orphan the
 * attribution on every 86 and Yes/No that person ever recorded. */
export const roster = {
  async list() {
    const { data, error } = await sb
      .from("managers")
      .select("id, email, full_name, role, active, user_id, created_at, deactivated_at, manager_stores(store_id)")
      .order("active", { ascending: false })
      .order("full_name", { nullsFirst: false });
    if (error) throw error;
    return data || [];
  },

  async add({ email, full_name, role, storeIds }) {
    const { data, error } = await sb
      .from("managers")
      .insert({ email: String(email).trim(), full_name: (full_name || "").trim() || null,
                role: role || "manager" })
      .select()
      .single();
    if (error) throw error;

    if (storeIds && storeIds.length) {
      const { error: e2 } = await sb.from("manager_stores")
        .insert(storeIds.map((s) => ({ manager_id: data.id, store_id: s })));
      if (e2) throw e2;   // the manager exists but is unassigned; the screen says so
    }
    return data;
  },

  // Reversible on purpose. Forgetting to revoke costs more than a mistaken tap,
  // and a mistaken tap is undone by the same button.
  async setActive(id, active) {
    const { data, error } = await sb
      .from("managers")
      .update({ active, deactivated_at: active ? null : new Date().toISOString() })
      .eq("id", id)
      .select()
      .single();
    if (error) throw error;
    return data;
  },

  async setRole(id, role) {
    const { data, error } = await sb
      .from("managers").update({ role }).eq("id", id).select().single();
    if (error) throw error;
    return data;
  },

  async assign(managerId, storeId) {
    const { error } = await sb.from("manager_stores")
      .insert({ manager_id: managerId, store_id: storeId });
    if (error && error.code !== "23505") throw error;   // already assigned is fine
  },

  async unassign(managerId, storeId) {
    const { error } = await sb.from("manager_stores")
      .delete().eq("manager_id", managerId).eq("store_id", storeId);
    if (error) throw error;
  },
};

export const client = sb;
