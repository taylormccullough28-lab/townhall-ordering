"""Whole-pipeline checks: nothing is dropped, and the seed calendar is right."""

from __future__ import annotations

from datetime import date, datetime

from thbev.depletion import DepletionEngine
from thbev.ingest import parse_item_selection_details
from thbev.ordering import OrderEngine, render_order
from thbev.sources import FileUploadSource

LOCATION = "Townhall - Short North"


def test_every_row_is_accounted_for(fixtures_dir, catalog):
    """Parsed, voided, filtered, dropped or unmapped -- but never just gone."""
    path = fixtures_dir / "item_selection_details.csv"
    data_rows = len(path.read_text(encoding="utf-8").strip().splitlines()) - 1
    parsed = parse_item_selection_details(path, location=LOCATION)
    accounted = (
        len(parsed.rows)
        + len(parsed.voided)
        + len(parsed.unmapped)
        + parsed.counters.get("rows_filtered_other_location", 0)
        + parsed.counters.get("totals_rows_dropped", 0)
    )
    assert accounted == data_rows

    depletion = DepletionEngine(catalog).deplete(parsed.rows)
    converted = {line.source_row for line in depletion.lines}
    queued = {row.row_number for row in depletion.unmapped}
    assert converted | queued == {row.row_number for row in parsed.rows}


def test_unmapped_quantities_are_visible_to_the_caller(fixtures_dir, catalog):
    parsed = parse_item_selection_details(
        fixtures_dir / "item_selection_details.csv", location=LOCATION
    )
    depletion = DepletionEngine(catalog).deplete(parsed.rows)
    assert sum(row.qty for row in depletion.unmapped) == 8
    assert depletion.summary()["unmapped_qty"] == 8


def test_full_pipeline_from_source_to_vendor_output(fixtures_dir, catalog):
    source = FileUploadSource(
        [fixtures_dir / "item_selection_history.csv"], location=LOCATION, cutoff_hour=4
    )
    sales = source.fetch_sales(date(2026, 7, 27), date(2026, 8, 30))
    depletion = DepletionEngine(catalog).deplete(sales.rows)
    orders = OrderEngine(catalog, depletion).suggest_all(
        at=datetime(2026, 8, 30, 16, 0), on_hand={"bud_light": 60}
    )
    superior = next(order for order in orders if order.vendor.key == "superior")
    output = render_order(superior)
    assert "Bud Light" in output.body
    assert superior.plan.days_of_cover == 7
    assert all(line.reasoning.one_liner() for line in superior.lines)


def test_seed_vendor_calendar_matches_the_order_guide(seed_catalog):
    """Seven cutoffs across four days. Missing one costs a week of that vendor.

    Order weekdays are operator-confirmed. Delivery weekdays were corrected on
    2026-09-29 from the written guide to what MarginEdge invoices actually show
    over 2026-08-28..09-28: nothing lands on Monday, and Tuesday takes six.
    """
    expected = {
        # Sunday 7pm lands Tuesday, not Monday - two nights of depletion to cover.
        ("superior", "superior_sunday"): (6, "19:00", 1),
        # Second window moved Thursday 5pm -> Wednesday 7pm (2026-09-21).
        ("superior", "superior_wednesday"): (2, "19:00", 4),
        ("columbus_distributing", "columbus_sunday"): (6, "19:00", 1),
        # Arena was never once observed delivering Monday across 13 invoices.
        ("arena", "arena_sunday"): (6, "17:00", 3),
        ("arena", "arena_wednesday"): (2, "21:00", 3),
        ("southern_glazers", "sgws_monday"): (0, "16:00", 1),
        # Sixth City delivers WEDNESDAY: 11 of 11 invoices over 2026-06-24..09-16.
        # This file and vendors.yaml both said Tuesday until 2026-10-01, while the
        # PRD appendix already said Wednesday. The invoices settle it.
        ("sixth_city", "sixth_city_monday"): (0, "17:00", 2),
        ("cavalier", "cavalier_monday"): (0, "17:00", 1),
        ("heidelberg", "heidelberg_wednesday"): (2, "17:00", 3),
        # Cafe. Berardi's cutoff confirmed Sunday 5pm by the operator 2026-09-29.
        ("berardis", "berardis_sunday"): (6, "17:00", 1),
        ("hartzler", "hartzler_thursday"): (3, "17:00", 1),
    }
    for (vendor_key, window_key), (weekday, order_time, delivery_weekday) in expected.items():
        window = seed_catalog.vendor(vendor_key).window(window_key)
        assert window.order_weekday == weekday
        assert window.order_time.strftime("%H:%M") == order_time
        assert window.delivery_weekday == delivery_weekday

    assert seed_catalog.vendor("oyo").windows == ()
    # Buckeye delivers Monday on 12 of 17 invoices but its cutoff has never been
    # recorded, so it carries no window rather than a guessed one.
    assert seed_catalog.vendor("buckeye").windows == ()
    followup = seed_catalog.vendor("southern_glazers").window("sgws_wednesday_followup")
    assert followup.requires_confirmation and followup.confirm_with == "Bethany"
