"""Accepted normalized header names, per logical field.

Every alias here was either observed verbatim in a recovered Toast export (see
the PRD ingest appendix) or is a defensive spelling of the same concept. Order
matters: the first alias present in a header row wins, so more specific
spellings are listed first.
"""

from __future__ import annotations

# --- PMIX: "All levels" sheet -------------------------------------------------
# Observed: Type | Menu | Menu group | Item, open item | Qty sold
# Variant also carrying: Subgroup | Avg. price | Gross sales | Net sales
ALL_LEVELS_ALIASES: dict[str, tuple[str, ...]] = {
    "type": ("type", "level", "row type"),
    "menu": ("menu",),
    "menu_group": ("menu group", "menugroup", "group"),
    "subgroup": ("subgroup", "sub group", "menu subgroup"),
    "menu_item": ("item open item", "menu item", "item name", "item"),
    "qty": ("qty sold", "quantity sold", "qty", "quantity"),
    "sales_category": ("sales category", "sales cat", "category"),
    "avg_price": ("avg price", "average price", "avg item price not incl mods"),
    "gross_sales": ("gross sales",),
    "net_sales": ("net sales",),
}

# --- PMIX: "Items" / "Open items" sheets --------------------------------------
# Observed: Item | Sales Category | Qty sold   (Sales Category is OPTIONAL)
ITEMS_ALIASES: dict[str, tuple[str, ...]] = {
    "menu_item": ("item open item", "menu item", "item name", "item"),
    "sales_category": ("sales category", "sales cat", "category"),
    "qty": ("qty sold", "quantity sold", "qty", "quantity"),
    "menu": ("menu",),
    "menu_group": ("menu group", "menugroup", "group"),
    "avg_price": ("avg price", "average price", "avg item price not incl mods"),
    "gross_sales": ("gross sales",),
    "net_sales": ("net sales",),
}

# --- PMIX: "Modifiers" sheet --------------------------------------------------
# No non-empty modifier export exists in the account yet; these aliases are a
# best-effort read of the sheet Toast produces so the parser does not crash the
# day one arrives. Anything it cannot classify goes to the unmapped queue.
MODIFIER_ALIASES: dict[str, tuple[str, ...]] = {
    "menu_item": ("modifier", "modifier name", "item open item", "item"),
    "parent_item": ("parent item", "parent menu item", "applied to"),
    "menu": ("menu",),
    "menu_group": ("menu group", "modifier group", "group"),
    "sales_category": ("sales category", "category"),
    "qty": ("qty sold", "quantity sold", "qty", "quantity"),
}

# --- ItemSelectionDetails CSV -------------------------------------------------
# Observed verbatim:
# Location,Order #,Sent Date,Menu Item,Menu Group,Menu,Sales Category,Net Price,Qty,Void?
ITEM_SELECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "location": ("location", "location name", "restaurant"),
    "order_id": ("order", "order id", "order number", "check"),
    "sent_date": ("sent date", "order date", "opened", "date"),
    "menu_item": ("menu item", "item open item", "item name", "item"),
    "menu_group": ("menu group", "menugroup", "group"),
    "menu": ("menu",),
    "sales_category": ("sales category", "sales cat", "category"),
    "net_price": ("net price", "price"),
    "qty": ("qty", "quantity", "qty sold"),
    "void": ("void", "voided", "is void"),
    # Not present in the recovered export, but Toast can emit them and comps
    # must be counted as depletion while staying flagged.
    "comp": ("comp", "comped", "is comp", "comped item"),
    "modifiers": ("modifiers", "modifier", "options"),
    "dining_option": ("dining option",),
}

# Values of the "Type" column on `All levels` that represent a real sale.
# Everything else -- including blank -- is a rollup subtotal and must not be
# counted, or every quantity double-counts.
LEAF_TYPES: frozenset[str] = frozenset({"menuitem", "openitem"})

# Normalized sheet names, mapped to the role the parser gives them.
SHEET_ROLES: dict[str, str] = {
    "all levels": "all_levels",
    "items": "items",
    "open items": "open_items",
    "modifiers": "modifiers",
    "special requests": "special_requests",
    "summary": "summary",
    "menus": "menus",
    "menu groups": "menu_groups",
}
