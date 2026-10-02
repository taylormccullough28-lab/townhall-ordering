"""ItemSelectionDetails CSV parsing: voids, locations, totals rows, timestamps."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from thbev.ingest import detect_format, parse_item_selection_details, parse_sent_date

LOCATION = "Townhall - Short North"


@pytest.fixture
def parsed(fixtures_dir):
    return parse_item_selection_details(
        fixtures_dir / "item_selection_details.csv", location=LOCATION, cutoff_hour=4
    )


def test_voids_are_excluded_and_kept_for_audit(parsed):
    assert parsed.counters["voids_excluded"] == 1
    assert all(not row.voided for row in parsed.rows)
    assert len(parsed.voided) == 1
    assert parsed.voided[0].qty == 6


def test_other_locations_are_filtered_out(parsed):
    assert parsed.counters["rows_filtered_other_location"] == 1
    assert all(row.location == LOCATION for row in parsed.rows)
    assert not any(row.qty == 99 for row in parsed.rows)


def test_trailing_totals_row_is_dropped(parsed):
    assert parsed.counters["totals_rows_dropped"] == 1
    assert not any(row.qty == 36 and row.key.menu_item is None for row in parsed.rows)


def test_late_night_sales_land_on_the_prior_business_day(parsed):
    late = [r for r in parsed.rows if r.sold_at == datetime(2026, 8, 31, 1, 30)]
    assert late and late[0].business_date == date(2026, 8, 30)
    early = [r for r in parsed.rows if r.sold_at == datetime(2026, 8, 31, 4, 5)]
    assert early and early[0].business_date == date(2026, 8, 31)


def test_same_item_carries_different_categories_on_different_menus(parsed):
    espolon = [r for r in parsed.rows if r.key.menu_item == "Espolon Blanco"]
    assert {r.key.sales_category for r in espolon} == {"Liquor", "Bottle Service"}
    assert {r.key.menu for r in espolon} == {"LIQUOR", "BOTTLE SERVICE"}


def test_blank_category_is_preserved(parsed):
    bacardi = [r for r in parsed.rows if r.key.menu_item == "Bacardi FB"]
    assert bacardi[0].key.sales_category is None
    assert bacardi[0].qty == 3


def test_business_date_range_filter(fixtures_dir):
    result = parse_item_selection_details(
        fixtures_dir / "item_selection_details.csv",
        location=LOCATION,
        start=date(2026, 8, 30),
        end=date(2026, 8, 30),
    )
    assert all(row.business_date == date(2026, 8, 30) for row in result.rows)
    assert result.counters["rows_outside_range"] == 1  # the 04:05 sale


def test_unknown_location_is_an_error_not_an_empty_success(fixtures_dir):
    result = parse_item_selection_details(
        fixtures_dir / "item_selection_details.csv", location="Nowhere"
    )
    assert not result.rows
    codes = {issue.code for issue in result.issues}
    assert "location_matched_nothing" in codes


def test_shuffled_columns_parse_identically(fixtures_dir):
    """Column order is scrambled and two extra columns exist."""
    result = parse_item_selection_details(
        fixtures_dir / "item_selection_details_with_mods.csv", location=LOCATION
    )
    assert result.counters["voids_excluded"] == 1
    assert result.counters["comps_included"] == 1
    comped = [r for r in result.rows if r.comped]
    assert comped[0].key.menu_item == "Bud Light" and comped[0].qty == 2
    mods = {r.order_id: r.modifiers for r in result.rows}
    assert mods["101"] == ("Single",)
    assert mods["102"] == ("Double",)
    assert mods["104"] == ()


def test_comps_can_be_excluded_by_config(fixtures_dir):
    result = parse_item_selection_details(
        fixtures_dir / "item_selection_details_with_mods.csv",
        location=LOCATION,
        include_comps=False,
    )
    assert not any(row.comped for row in result.rows)
    assert result.counters["comps_excluded_by_config"] == 1


@pytest.mark.parametrize(
    "text, expected",
    [
        ("8/27/2023 9:06", datetime(2023, 8, 27, 9, 6)),
        ("8/27/2023 19:10", datetime(2023, 8, 27, 19, 10)),
        ("2026-08-30 21:00", datetime(2026, 8, 30, 21, 0)),
        ("nonsense", None),
        ("", None),
    ],
)
def test_sent_date_parsing(text, expected):
    assert parse_sent_date(text) == expected


def test_format_detection(fixtures_dir):
    assert detect_format(fixtures_dir / "item_selection_details.csv") == "item_selection_details"
    assert detect_format(fixtures_dir / "pmix_full.xlsx") == "pmix"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_item_selection_details(tmp_path / "nope.csv")


def test_unrecognizable_header_raises(tmp_path):
    path = tmp_path / "junk.csv"
    path.write_text("alpha,beta\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_item_selection_details(path)
