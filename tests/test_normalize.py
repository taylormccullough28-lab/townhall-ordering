"""Header normalization and named column resolution.

A positional parser breaks on the second Toast file it ever sees, so these are
the guards that keep column lookup name-based.
"""

from __future__ import annotations

import pytest

from thbev.ingest.columns import ALL_LEVELS_ALIASES, ITEM_SELECTION_ALIASES
from thbev.normalize import (
    cell,
    normalize_header,
    parse_bool,
    parse_number,
    resolve_columns,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Item, open item", "item open item"),
        ("  Qty sold  ", "qty sold"),
        ("Void?", "void"),
        ("Avg. price", "avg price"),
        ("Avg. item price (not incl. mods)", "avg item price not incl mods"),
        ("Order #", "order"),
        ("MENU GROUP", "menu group"),
        (None, ""),
    ],
)
def test_header_normalization(raw, expected):
    assert normalize_header(raw) == expected


def test_columns_resolve_regardless_of_order():
    forward = ["Type", "Menu", "Menu group", "Item, open item", "Qty sold"]
    shuffled = ["Qty sold", "Item, open item", "Menu group", "Type", "Menu"]
    a, _, _ = resolve_columns(forward, ALL_LEVELS_ALIASES)
    b, _, _ = resolve_columns(shuffled, ALL_LEVELS_ALIASES)
    assert a["qty"] == 4 and b["qty"] == 0
    assert a.keys() == b.keys()


def test_missing_columns_are_reported_not_raised():
    bound, missing, unrecognized = resolve_columns(["Item", "Qty sold"], ALL_LEVELS_ALIASES)
    assert "menu_item" in bound and "qty" in bound
    assert "sales_category" in missing and "type" in missing
    assert unrecognized == []


def test_unrecognized_columns_are_surfaced():
    _, _, unrecognized = resolve_columns(
        ["Menu Item", "Qty", "Tax Amount"], ITEM_SELECTION_ALIASES
    )
    assert unrecognized == ["tax amount"]


def test_more_specific_alias_wins():
    bound, _, _ = resolve_columns(["Item", "Menu Item", "Qty"], ITEM_SELECTION_ALIASES)
    assert bound["menu_item"] == 1  # "Menu Item", not the bare "Item"


def test_cell_tolerates_short_rows():
    bound = {"qty": 4}
    assert cell(["a", "b"], bound, "qty") is None
    assert cell(["a", "b"], bound, "absent") is None


@pytest.mark.parametrize(
    "raw, expected",
    [("TRUE", True), ("false", False), ("Yes", True), ("", False), ("maybe", None), (None, None)],
)
def test_bool_parsing(raw, expected):
    assert parse_bool(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [("1,234", 1234.0), ("$8.75", 8.75), ("(3)", -3.0), ("", None), ("abc", None), (7, 7.0)],
)
def test_number_parsing(raw, expected):
    assert parse_number(raw) == expected
