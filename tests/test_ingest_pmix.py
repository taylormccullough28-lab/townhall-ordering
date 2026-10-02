"""PMIX workbook parsing.

The failure mode this file guards against is silent: a parser that reads the
`All levels` sheet without filtering on `Type` returns numbers that look
plausible and are roughly double.
"""

from __future__ import annotations

import pytest

from thbev.ingest import parse_pmix
from thbev.models import Severity


@pytest.fixture
def full(fixtures_dir):
    return parse_pmix(fixtures_dir / "pmix_full.xlsx")


def test_rollup_rows_are_not_counted(full):
    """Blank-Type rows are subtotals. Counting them double-counts everything."""
    espolon = [row.qty for row in full.rows if row.key.menu_item == "Espolon Blanco"]
    assert sorted(espolon) == [2, 193]  # two leaf rows, on two different menus
    assert [row.qty for row in full.rows if row.key.menu_item == "Bud Light"] == [187]
    # The rollups say LIQUOR=400 and Tequila=193. Neither may appear as a row.
    assert all(row.key.menu_item for row in full.rows)
    assert full.counters["rollup_rows_skipped"] == 6
    # 193 + 4 + 34 + 187 + 23 + 3 + 2 leaf quantities only.
    assert full.total_qty == 446


def test_leaf_types_include_open_items(full):
    sources = {row.key.menu_item for row in full.rows}
    assert "Lobos Blanco Bottle" in sources


def test_totals_row_is_dropped(full):
    assert full.counters["totals_rows_dropped"] == 1
    assert not any(row.qty == 446 for row in full.rows)


def test_blank_sales_category_survives(fixtures_dir):
    """`Bacardi FB`, qty 4, no category. Filtering on category drops real liquor."""
    result = parse_pmix(fixtures_dir / "pmix_full.xlsx", prefer="items")
    bacardi = [r for r in result.rows if r.key.menu_item == "Bacardi FB"]
    assert len(bacardi) == 1
    assert bacardi[0].qty == 4
    assert bacardi[0].key.sales_category is None


def test_menu_structure_is_preserved_for_the_composite_key(full):
    espolon = sorted(
        (r for r in full.rows if r.key.menu_item == "Espolon Blanco"), key=lambda r: r.qty
    )
    assert [r.key.menu for r in espolon] == ["BOTTLE SERVICE", "LIQUOR"]
    assert [r.key.menu_group for r in espolon] == ["Tequila Bottles", "Tequila"]


def test_columns_are_matched_by_name_not_position(fixtures_dir):
    """The variant file reorders columns and drops Sales Category entirely."""
    variant = parse_pmix(fixtures_dir / "pmix_variant_subgroup_no_category.xlsx")
    by_item = {row.key.menu_item: row for row in variant.rows}
    assert by_item["Espolon Blanco"].qty == 193
    assert by_item["Bud Light"].qty == 187
    # Subgroup exists here and is folded into the group slot for extra specificity.
    assert by_item["Espolon Blanco"].key.menu_group == "Tequila / Blanco"
    # No Sales Category column anywhere in this export.
    assert all(row.key.sales_category is None for row in variant.rows)


def test_missing_sales_category_is_reported_not_fatal(fixtures_dir):
    variant = parse_pmix(fixtures_dir / "pmix_variant_subgroup_no_category.xlsx")
    codes = {issue.code for issue in variant.issues}
    assert "sheet_absent" in codes  # Modifiers / Special requests are gone
    assert variant.rows


def test_items_sheet_column_order_does_not_matter(fixtures_dir):
    """The variant Items sheet is `Qty sold | Item` -- reversed."""
    variant = parse_pmix(fixtures_dir / "pmix_variant_subgroup_no_category.xlsx", prefer="items")
    by_item = {row.key.menu_item: row.qty for row in variant.rows}
    assert by_item == {"Espolon Blanco": 193, "Bacardi FB": 4, "Bud Light": 187}


def test_all_levels_without_type_is_refused_loudly(fixtures_dir):
    """No Type column means rollups and leaves are indistinguishable."""
    result = parse_pmix(fixtures_dir / "pmix_all_levels_no_type.xlsx")
    errors = [i for i in result.issues if i.code == "all_levels_no_type_column"]
    assert errors and errors[0].severity is Severity.ERROR
    assert result.counters["all_levels_rows_skipped_no_type"] == 3
    # It falls back to the Items sheet rather than returning nothing.
    assert "Items" in result.sheets_used
    assert {r.key.menu_item for r in result.rows} >= {"Bud Light", "Espolon Blanco"}


def test_empty_modifiers_sheet_is_reported(full):
    codes = {issue.code for issue in full.issues}
    assert "modifiers_sheet_empty" in codes


def test_pmix_rows_carry_no_time_dimension(full):
    assert not full.has_time_dimension
    assert all(row.business_date is None for row in full.rows)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_pmix(tmp_path / "nope.xlsx")
