---
name: menu-ordering-prototype
description: Build an interactive, self-contained HTML test-ordering app from a restaurant or cafe menu file (PDF, doc, or similar) — extracts every item, price, dietary tag, and modifier, then generates a working browse-to-checkout prototype with live pricing, "build-your-own" customization, time-gated menu sections, and allergen/food-safety disclaimers. Use this whenever the user hands you a menu and asks to build, prototype, mock up, or test an online ordering experience — including requests like "build an ordering app for this menu," "let me practice ordering from this," or "make this menu clickable" — even if they don't say "skill" or use these exact words. Also use it when updating an existing menu-ordering prototype for a new location, daypart, or menu revision.
---

# Menu Ordering Prototype

Turn a restaurant/cafe menu file into a working, interactive test-ordering web app — the kind a stakeholder can click through to feel out an ordering flow before any real backend, POS integration, or payment processing exists.

## Why this workflow, not a from-scratch build

A real menu is mostly *data* (items, prices, tags, modifier rules) wearing a thin layer of *interaction* (pick one, pick up to three, add $2 if you go past two). Hand-coding each item's markup gets unmanageable fast and makes prices easy to get wrong. Instead: extract the menu into a structured data array, and drive one generic rendering + pricing engine off of it. `assets/ordering-app-template.html` already has that engine built, tested, and debugged — start from it rather than reinventing it.

## Step 1 — Read the menu completely before writing any code

Use the `Read` tool directly on the menu file (it handles PDFs natively — don't shell out to a converter). Read every page; menus often repeat a legend/footnote per page but have real per-item differences page to page.

For every item, capture:
- **Name, price, description**
- **Dietary/allergen tags** (whatever legend the menu uses — GF, V, N, keto, etc.) — these matter more than they look like they do. A real diner filters on them, and the source usually carries a liability disclaimer (cross-contact, raw/undercooked) that has to survive into the app, not just live in a footnote no one reads.
- **Every priced modifier**: bun/side/protein swaps, add-ons, "upgrade your X" lists, build-your-own choice groups. Note for each group:
  - Is it single-select (radio) or multi-select (checkbox)?
  - Is a choice required, or optional?
  - Is there a cap ("choose up to 3")?
  - Is there a "first N are free, then +$X each" rule? (Common on build-your-own bowls/sides — get this exactly right, it's the easiest place to misprice an order.)
- **Time/availability gating** — sections like "served after 5pm" or dayparts. Note the exact cutoff.
- **Items that aren't fully specified on the page** — "ask your server," rotating specials. Don't invent specifics for these; flag them honestly in the app instead (see Step 3).

If the user only gives you a folder ("check my Downloads") rather than a specific file, don't guess blind — `ls`/`find` for candidates, prefer the most recently modified matching file, and say plainly which file and date you built from. Menus get revised constantly; a stale source produces a confidently wrong app.

## Step 2 — Shape the extracted menu into data, not markup

Copy `assets/ordering-app-template.html` as your starting point. It already implements:
- A `MENU` array of `{ id, label, items }` categories, each item having `{ id, name, price, tags, desc, groups, asterisk, servedAfter, askServer }`.
- A `groups` schema for modifiers — build every choice group (swap, add-on, build-your-own step) as one of these, don't invent a new shape per item:
  ```js
  { key, label, type: 'single'|'multi', options: [{id, label, price, tags}],
    required, min, max, extraChargeAfter, extraChargePrice }
  ```
  `extraChargeAfter` + `extraChargePrice` is what encodes "first 2 free, then +$3 each" — set `extraChargeAfter` to the free count and it's handled automatically by the pricing engine.
- A generic pricing engine (`computeModPrice`, `itemUnitPrice`) that sums base price + every selected modifier, respecting the free-count rule — you should never need to hand-write per-item price math.
- Item cards, a customize panel (radio/checkbox per group, live-updating total, required-group validation gating "Add to Cart"), a cart with itemized modifier lines, a 2.9%-style transaction-fee line (adjust or remove the fee/rate to match what the real menu discloses), and a simulated checkout that produces a clearly-labeled *test/practice* receipt — no real payment, no real order transmission, no invented POS integration.
- Session-scoped allergen/cross-contact banner + a dietary legend modal, sourced from whatever legend the real menu prints.

Do the actual work of **replacing the `MENU` array and the brand/header strings** with what you extracted in Step 1. Resist the urge to also rewrite the engine functions unless the new menu genuinely needs a modifier shape the schema can't express — in that case, extend the schema (add a field), don't fork a parallel system.

For items marked "ask your server" or otherwise unspecified, set `askServer: true` rather than fabricating a specific answer — the template already renders an honest "confirmed by staff at pickup" note for these instead of a fake guarantee.

For time-gated sections (`servedAfter`), gate against the **guest's selected pickup time**, not the real wall-clock time — someone ordering at 2pm for 6pm pickup should still be able to order dinner items. The template's `pickupMeetsGate()` already does this; just set `servedAfter` on the category/item.

## Step 3 — Test it interactively before calling it done

Don't just eyeball the generated HTML — open it in the Browser pane and actually drive it:
1. Click through category nav to confirm every section renders.
2. Open the most complex build-your-own item and complete a full customization — pick options with non-zero prices, hand-calculate the expected total, and check it matches the live total shown in the panel.
3. Confirm required-group validation actually blocks "Add to Cart" until satisfied, and that it un-blocks once satisfied.
4. If there's time-gating, test it both ways: select a pickup time before the cutoff (item should show locked/unavailable with a clear reason) and at/after the cutoff (item should unlock).
5. Add an item to cart, open the cart, confirm the fee and total math, and complete a full "place order" to confirm the receipt renders with the right order details and is clearly labeled as a test/practice order.

**Known pitfall — verify this specifically:** if you modify the template's rendering functions at all, re-check that selecting an option inside the customize panel or adjusting cart quantities doesn't reset scroll to the top. The template captures and restores `scrollTop` across re-renders for exactly this reason (`renderItemModal` and `openCart` both do this) — a naive `innerHTML` replacement on every change will silently reintroduce this bug and make any multi-group builder painful to use.

## Common pitfalls (from building the TownHall CLE prototype)

- **Don't flatten "choose 2, then +$3 each additional" into a flat surcharge.** It's genuinely a per-selection-index rule, not a per-item one — encode it with `extraChargeAfter`/`extraChargePrice`, not a fixed add-on price.
- **Don't gate time-sensitive sections on `Date.now()`/real clock time.** Gate on the pickup time the guest actually selected.
- **Don't silently drop "ask your server" items** to keep the data clean — mark them and say so in the UI; omitting them makes the app look more complete than the real menu is.
- **Don't skip the disclaimers.** Cross-contact/allergen and raw-or-undercooked-ingredient warnings aren't decoration — carry them from the source menu into the app, at the banner level and at add-to-cart for flagged items.
- **Don't assume Vercel/CSP-style strict environments when this is a local/offline test build.** The template uses a Google Fonts `<link>` for typography, which is fine for a locally-opened file or a normal web deploy — but won't load inside a sandboxed artifact iframe with a strict CSP. If the user asks you to publish this as a Claude Artifact specifically, swap to a system-font stack and inline everything; don't assume the file's current form ports over unchanged.
- **State the source file and its date explicitly** in your summary to the user, since menus in a shared Downloads folder are usually one of many dated revisions.
