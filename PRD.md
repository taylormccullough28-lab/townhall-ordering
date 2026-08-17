# PRD: TownHall Online Ordering

**Status:** Draft — scoped as a test build · **Owner:** TBD · **Last updated:** 2026-08-17

**Source menu:** `th.CLE.dinner.menu.5.1.26.pdf` — TownHall CLE, dinner menu, dated 5.1.26 (the most recently modified full dinner menu found in Downloads). This PRD is scoped to CLE only.

**Scope decisions (confirmed):**
- CLE location only — no other locations in scope.
- First-party ordering only — this is not an integration with or replacement for third-party delivery marketplaces (DoorDash/UberEats); it's a standalone direct-to-guest channel.
- This is a test build for exploring what the app looks like, not a production launch — see the P0 table for what's simulated vs. real in this phase.

---

## Problem Statement

TownHall's dine-in menu is built almost entirely around customization — build-your-own bowls, protein and bun swaps, sauce/garnish/side choices, functional supplement add-ons — none of which exists today as a way to order ahead. Customers who want TownHall without dining in have to either call in and describe a highly configurable order verbally, or go through a third-party delivery app (evidence in this account's own files: recurring "3rd party togos" and "DD/UE report" tracking) that takes a commission and typically can't represent the menu's full complexity anyway. The result is lost direct revenue, order errors on complex items, and no first-party relationship with the ordering customer.

## Goals

- Let a guest place a fully customized order (build-your-own bowl, protein/bun/side swaps, add-ons) online with the same configurability they'd get ordering in person — no "call the restaurant to modify" fallback.
- Reduce reliance on third-party delivery marketplaces for orders TownHall could capture directly, by giving guests a first-party ordering path.
- Get accurate, unambiguous dietary/allergen information (GF, vegan, nut-contains, keto/paleo) in front of guests before they order, given the kitchen's explicit cross-contact disclaimer.
- Keep menu content (items, prices, availability, modifiers) easy to update without an engineering change, given how frequently this menu actually changes (dozens of dated revisions found for this single location in the last year alone).
- Get orders to checkout with a correct total on the first try — every modifier price delta, upcharge, and the disclosed 2.9% transaction fee reflected accurately, so there are no surprises at pickup or on the card statement.

## Non-Goals

- **Not a delivery logistics system.** Whether fulfillment is pickup-only, TownHall-run delivery, or a courier integration (DoorDash Drive, Uber Direct) is out of scope for this PRD — flagged as an open question, not decided here.
- **Not a reservations or waitlist system.** This is strictly food/beverage ordering, not table management.
- **Not a POS replacement, and not POS-integrated in this test build.** A real launch would need POS integration for menu sync and order injection, but for this test the menu is maintained directly rather than pulled live from a POS.
- **Not multi-location.** Scoped to TownHall CLE only — confirmed, not just a v1 default.
- **Not integrated with third-party delivery marketplaces.** This is a first-party-only ordering channel; DoorDash/UberEats are out of scope entirely, not a future integration target.
- **Not other dayparts.** Brunch, late night, and sushi menus exist as separate documents at this location but are out of scope — this PRD covers the dinner menu only.
- **Not a loyalty/rewards program.** No points, tiers, or repeat-visit incentives.

## Target Users

- **Primary:** TownHall guests who already know the menu and want to order ahead for pickup — regulars ordering their usual build-your-own bowl or a Mains dish.
- **Secondary:** First-time online orderers unfamiliar with the menu's build-your-own mechanics and dietary tagging, who need the UI itself to teach them the choices (base → protein → sauce → garnish → sides).
- **Internal:** Kitchen/front-of-house staff who receive and fulfill the order — not a designer of the experience, but a hard constraint on what "done" looks like (order must arrive in a format the kitchen can act on without re-keying it).

## User Stories

- As a guest, I want to browse the menu by category (Shareables, Bowls, Handhelds, Mains, etc.) so I can find what I want the way I would on the physical menu.
- As a guest, I want to see dietary tags (GF, V, K, N, etc.) on every item and have the legend available, so I can filter to what's safe/appropriate for me without guessing.
- As a guest with a nut allergy, I want a visible cross-contact warning before I check out, so I can make an informed decision — not discover it after ordering.
- As a guest, I want to build my own bowl by choosing a base, protein, sauce, up to three garnishes, and up to two sides, with the price updating as I go, so the total is never a surprise.
- As a guest, I want to swap a burger's bun (lettuce, vegan +2, keto avo +3, sweet potato waffle +4) or upgrade a handheld's side, so my order matches how I'd customize it in person.
- As a guest, I want to add functional add-ons (collagen, creatine, CBD oil, etc.) to a drink or bowl, so I can replicate the in-store "wellness bar" experience.
- As a guest ordering before 5pm, I want Mains-section items marked unavailable (with a clear reason) rather than orderable-then-cancelled, so I'm not misled about what I can actually get right now.
- As a guest, I want the order summary and receipt to clearly show the 2.9% transaction fee before I confirm payment, matching TownHall's posted disclosure.
- As a guest ordering a raw/undercooked item (steak, salmon, poke, a cheeseburger cooked to temp), I want to see the food-safety disclaimer at the point of ordering, not buried in fine print.
- As a returning guest, I want to reorder a past customized order (e.g. my exact bowl build) in one action, so I don't have to reconfigure it every time.
- As kitchen/FOH staff, I want an incoming online order to show every modifier explicitly and unambiguously (not as a free-text note), so it can be prepped correctly without a phone call back to the guest.

## Requirements

### Must-Have (P0)

| Requirement | Acceptance Criteria |
|---|---|
| Category-based menu browsing | All dinner-menu categories are browsable (Shareables, Soups, Flatbreads, Bowls + Greens, Build-Your-Own Bowl, Bone Broths, Handhelds, Mains, Sides, Smoothies, Coffee/Lattes, Matcha + Teas, Water, Juices, Bakery/desserts, Shakes), matching the source menu's structure. |
| Item detail with dietary tags | Every item displays its full tag set (GF/GFA/N/V/VA/P/PA/K/KA) with the legend accessible from any screen, not just the menu top. |
| Cross-contact / allergen disclaimer | The kitchen's "not a nut or gluten-free kitchen" disclaimer is shown once per order session before checkout, not just in menu footer text. |
| Raw/undercooked disclaimer | Any asterisked item (Wagyu Steak, Wild Salmon, Wild Poke, Cheeseburger) surfaces the food-safety disclaimer at add-to-cart, not only in menu fine print. |
| Build-Your-Own Bowl flow | Guest selects exactly 1 base, 1 protein, 1 sauce, up to 3 garnishes, up to 2 sides, with a double-protein option and extra-side upcharge, and the running price updates live to match the $16 base + variable pricing structure. |
| Build-Your-Own Flatbread flow | Guest starts from the $12 base and adds any number of $2 toppings (or +$3 for paleo crust), with live price updates. |
| Build-Your-Own Bone Broth flow | Guest picks a $5/$10 (12oz/32oz) base broth and any combination of priced add-ons (from $0.50 to $2 each). |
| Modifier price accuracy | Every priced modifier in the source menu (bun upgrades, side upgrades, protein upgrades, milk substitutions, noodle upgrades, add-ons) is represented with its exact price delta — no flat "customization fee" approximations. |
| Time-gated availability (Mains) | Items under "Mains" are only orderable for pickup times at or after 5:00 PM local time; attempting to order earlier shows why, rather than silently blocking or allowing an invalid order. |
| Transaction fee disclosure | The 2.9% transaction fee is shown as a line item in the order summary before payment is confirmed, matching the posted menu disclosure. |
| Accurate order total at checkout | The final charged total exactly matches the sum of base item price + all selected modifiers + transaction fee, with no rounding or approximation drift. |
| Order handoff (simulated for this test build) | A submitted order produces a structured, itemized summary (not free text) listing every selected modifier per item — good enough to prove the ordering flow captures orders unambiguously. Real POS/kitchen integration is out of scope for this phase. |
| "Ask your server" items handled honestly | Items whose full detail isn't captured in the menu data (e.g. "Vegan Dessert of the Week — ask for details," "Organic Hot Teas — ask server for selections") are either resolved with real current data or clearly marked as call/contact-required rather than silently omitted or falsely presented as fully specified. |

### Nice-to-Have (P1)

| Requirement | Notes |
|---|---|
| Saved/repeat orders | Let a returning guest reorder a previous customized order (especially a Build-Your-Own Bowl) in one step. |
| Dietary filtering | Filter the whole menu by tag (e.g. "show me everything Keto-Friendly") rather than only reading tags item-by-item. |
| Order status tracking | Guest sees order state (received → preparing → ready for pickup) rather than just a confirmation screen. |
| Guest accounts | Optional login to store order history and default payment method, without requiring an account to order. |

### Future Considerations (P2)

| Requirement | Notes |
|---|---|
| Multi-location support | Location picker driving which menu (and which time-gating rules) apply — deferred until the CLE-only v1 is validated. |
| Additional dayparts | Brunch, late-night, and sushi menus exist as separate documents at this location and could be added as additional time-gated menu sets once dinner ordering is proven. |
| Delivery fulfillment | TownHall-run or courier-integrated delivery, as opposed to pickup-only — deliberately deferred, not decided against. |
| Loyalty / repeat-visit incentives | Points, rewards, or subscription-style perks for frequent online orderers. |

## Success Metrics

**Leading indicators**
- % of started orders that reach checkout (cart abandonment, especially within the Build-Your-Own Bowl/Flatbread flows, which are the most complex interactions).
- % of orders requiring a manual phone call to clarify a modifier (target: as close to zero as possible — any non-zero rate signals the structured-modifier UI isn't capturing intent correctly).
- Average time to complete a Build-Your-Own Bowl order.
- % of orders placed with at least one customization/modifier (signal for whether the flexible-ordering value prop is actually being used).

**Lagging indicators**
- First-party online order volume as a share of total off-premise orders, relative to third-party delivery volume (directly tied to the goal of reducing third-party dependency).
- Order accuracy at fulfillment (kitchen-reported errors traced to online orders vs. in-person/phone orders).
- Repeat online-order rate within 30 days of a first online order.

*Note: none of this is measurable without analytics/order-logging instrumentation, which this PRD assumes will exist but does not itself specify.*

## Open Questions

**Resolved:**
- ~~Replace/supplement third-party delivery?~~ → First-party only; no DoorDash/UberEats integration.
- ~~Which location(s) / dayparts in scope?~~ → CLE dinner menu only.
- ~~POS integration now or later?~~ → Not for this test build; menu is maintained directly for now. Real POS sync is a production-readiness question, not a test-build one.

**Still open:**
- **[Operations]** Fulfillment model: pickup-only, or does delivery need solving too? (Still relevant even first-party-only — TownHall could run its own delivery.)
- **[Legal/Compliance]** Who owns sign-off on the food-safety and allergen disclaimer language and placement in the ordering flow?
- **[Product]** For "ask your server" items (rotating vegan dessert, hot tea selection) — resolved with real current data, or excluded from ordering until fully specified?
- **[Product]** For this test build specifically — is the goal a working prototype to demo/react to, or does it need to handle real payments and real orders at any point?

## Timeline Considerations

- No hard external deadline; this is a test build, not a scheduled launch.
- Recommended phasing: **Phase 1 (this PRD)** — CLE dinner menu, first-party, pickup-only, P0 requirements, order handoff simulated rather than POS-integrated. **Phase 2** — P1 items (saved orders, filtering, status tracking) once the core flow is validated. **Phase 3** — real POS integration, payments, and any of the still-open questions above, only if this moves toward production.

## Appendix: Source Menu Structure

Pulled directly from `th.CLE.dinner.menu.5.1.26.pdf` to ground the requirements above:

- **Shareables:** Dip Trilogy, Keto Baked Buffalo Tenders, Sweet Potato Skins 2.0, Buffalo Cauliflower Lettuce Wraps, Keto Chicken Wings, Tallow Truffle Fries, Chili + Queso Loaded Nachos, Steak Bites by Stano, Organic Hummus
- **Soups / Bone Broths:** Jalapeño Garlic + Mushroom, Spicy Chicken Noodle, Organic Collagen Bone Broth (build-your-own with add-ons), Vegan Chili, Tomato Bisque
- **Flatbreads:** Classico, Korean BBQ, Green Envy, Build-Your-Own ($12 base + $2/topping, +$3 paleo crust)
- **Bowls + Greens:** Wild Poke 2.0*, Chopped Salad, Harvest Salad, Keto Mediterranean Salad, Thai Peanut, Bangkok Bazaar
- **Build-Your-Own Bowl ($16 base):** Base (5 options) → Protein (9 options, some +price) → Sauce (7 options) → Garnish (choose 3, 8 options) → Sides (choose 2, 5 options, +$3 extra); double-protein option
- **Handhelds:** Grass-Fed Cheeseburger*, Paleo Carnivore Smashburger, TownHall Veggie Burger, Nashville Chicken Sandwich, Quesabirria Tacos (choose protein), Grilled Cheese Bars + Tomato Bisque — with bun upgrades (+2 to +4) and side upgrades (+2 to +3)
- **Mains (served after 5pm only):** Grass-Fed Wagyu Steak*, Keto Fried Chicken, Wild Salmon* — each with a wild shrimp add-on
- **Sides:** Carnivore proteins (steak bites, burger patty, chicken thigh/breast, shrimp, salmon) and Optimal vegetable/mash sides
- **Smoothies (Rx):** Matcha Glow, Strawberry Skin Renewal, Longevity, Being Brigid 2.0, Keto Protein Powerhouse 2.0
- **Coffee / Lattes / Bulletproof:** Drip, Espresso, Nature's Adderall cold brew, several lattes, Bulletproof coffee variants, cold foam upgrades
- **Water:** Reverse Osmosis Structured (sparkling/still), Hydrogen Water, Mountain Valley Spring Water
- **Juices + Refreshments:** Wellness/Wheatgrass shots, fresh juices, organic iced teas, several lemonades
- **Matcha + Teas:** Organic Matcha, Matcha Latte, Iced Keto Vanilla Protein Matcha, Iced Strawberry Matcha Latte, Chai Latte, Organic Hot Teas (server-selected)
- **Milk options:** Whole (local pasture-raised), Oat (+1.50), Almond (+1.50), Keto Coconut (+1)
- **Functional Add-Ons:** ~15 supplement-style add-ons ($1–$4): colostrum, protein powder, collagen creamer, amino greens, nootropic, creatine, base ketones, vegan protein, CBD oil, cacao, ghee, sea moss, maca, MCT oil, caffeine, cashew butter
- **Bakery / Sweet Endings:** Skillet cookies, Chocolate Brownie Sundae, TownHall Butter Cake, Açaí Bowl, Keto Chocolate Cheesecake, Keto Buckeye/Energy Bites, Keto Protein Cookie Dough, standard/paleo chocolate chip cookies, Chocolate Fudge Brownie, rotating Vegan Dessert of the Week
- **Shakes:** Classic (Chocolate/Strawberry/Vanilla), House (Wild Berry Crumble, Peanut Butter Honey Graham)
- **Compliance/disclosure text present on the source menu:** allergen tag legend (repeated per page), "TownHall is not a nut or gluten-free kitchen" cross-contact warning, 2.9% transaction fee disclosure (all transactions, regardless of payment method), raw/undercooked-ingredient disclaimer for asterisked items
