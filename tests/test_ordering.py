"""Order suggestion: the arithmetic, the reasoning record, and the vendor rules."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from thbev.ordering import DayContext, OrderEngine, Weather, emergency_contact, render_order

SUNDAY_4PM = datetime(2026, 8, 30, 16, 0)


@pytest.fixture
def engine(catalog, history_depletion):
    return OrderEngine(catalog, history_depletion)


def line_for(order, product_key):
    return next(line for line in order.lines if line.product.key == product_key)


# -- the core arithmetic -----------------------------------------------------


def test_order_covers_to_the_next_delivery_not_a_flat_week(engine):
    week = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    four_days = engine.suggest_vendor("superior", at=SUNDAY_4PM, include_optional_windows=True)
    assert week.plan.days_of_cover == 7
    assert four_days.plan.days_of_cover == 4
    assert line_for(four_days, "bud_light").order_packs < line_for(week, "bud_light").order_packs


def test_safety_stock_is_a_quarter_of_forecast_with_a_floor_of_one(engine, catalog):
    order = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    reasoning = line_for(order, "bud_light").reasoning
    assert reasoning.safety_stock == pytest.approx(reasoning.forecast_over_cover * 0.25)
    # The floor applies literally, even with no forecast at all -- and the line
    # says so rather than quietly buying a case of a dead SKU.
    quiet = engine.suggest_vendor("southern_glazers", at=SUNDAY_4PM)
    bacardi = line_for(quiet, "bacardi_750")
    assert bacardi.reasoning.forecast_over_cover == 0.0
    assert bacardi.reasoning.safety_stock == 1.0
    assert any("safety floor" in warning for warning in bacardi.warnings)


def test_on_hand_and_on_order_reduce_the_need(engine):
    bare = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    stocked = engine.suggest_vendor(
        "superior", at=SUNDAY_4PM, on_hand={"bud_light": 400}, on_order={"bud_light": 48}
    )
    assert line_for(stocked, "bud_light").order_packs < line_for(bare, "bud_light").order_packs
    reasoning = line_for(stocked, "bud_light").reasoning
    assert reasoning.counted_on_hand == 400
    assert reasoning.already_on_order == 48


def test_quantities_round_up_to_pack_size(engine, catalog):
    order = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    for line in order.lines:
        assert line.order_units == line.order_packs * line.product.pack_size
        assert line.order_units >= line.reasoning.need_units - 1e-9
    assert catalog.product("bud_light").pack_size == 24
    assert catalog.product("nutrl").pack_size == 6


def test_post_cutoff_adjustment_lowers_effective_on_hand(engine):
    """An order placed at 4pm Sunday is placed while the bar is still selling."""
    order = engine.suggest_vendor(
        "superior", at=SUNDAY_4PM, on_hand={"bud_light": 100}, counted_at=SUNDAY_4PM
    )
    reasoning = line_for(order, "bud_light").reasoning
    assert reasoning.post_cutoff["available"] is True
    assert reasoning.effective_on_hand < 100
    assert reasoning.post_cutoff["units"] > 0
    assert not order.warnings


def test_post_cutoff_adjustment_says_so_when_it_cannot_run(catalog, fixtures_dir):
    """A PMIX-only ingest has no time dimension. Warn loudly; never fake a curve."""
    from thbev.depletion import DepletionEngine
    from thbev.ingest import parse_pmix

    depletion = DepletionEngine(catalog).deplete(parse_pmix(fixtures_dir / "pmix_full.xlsx").rows)
    order = OrderEngine(catalog, depletion, open_days=[date(2026, 8, 30)]).suggest_vendor(
        "superior", at=SUNDAY_4PM, on_hand={"bud_light": 100}
    )
    reasoning = line_for(order, "bud_light").reasoning
    assert reasoning.post_cutoff["available"] is False
    assert reasoning.effective_on_hand == 100
    assert any("Post-cutoff" in warning for warning in order.warnings)


def test_strict_mode_raises_instead_of_warning(catalog, fixtures_dir):
    from thbev.depletion import DepletionEngine
    from thbev.ingest import parse_pmix
    from thbev.ordering import PostCutoffUnavailable

    depletion = DepletionEngine(catalog).deplete(parse_pmix(fixtures_dir / "pmix_full.xlsx").rows)
    engine = OrderEngine(catalog, depletion, open_days=[date(2026, 8, 30)])
    with pytest.raises(PostCutoffUnavailable):
        engine.suggest_vendor("superior", at=SUNDAY_4PM, strict_post_cutoff=True)


def test_events_move_the_quantities(engine):
    calendar = {
        day: DayContext(day=day, events=["osu_home_football"])
        for day in [date(2026, 9, 5)]
    }
    plain = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    game = engine.suggest_vendor("superior", at=SUNDAY_4PM, calendar=calendar)
    assert line_for(game, "bud_light").order_packs > line_for(plain, "bud_light").order_packs
    drivers = [
        m.driver
        for day in line_for(game, "bud_light").reasoning.forecast.days
        for m in day.multipliers
    ]
    assert "osu_home_football" in drivers


def test_weather_moves_seltzer_and_brown_spirits_in_opposite_directions(engine, catalog):
    hot = {
        day: DayContext(day=day, weather=Weather(high_f=92, sunny=True))
        for day in [date(2026, 8, 31) , date(2026, 9, 1)]
    }
    plain = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    warm = engine.suggest_vendor("superior", at=SUNDAY_4PM, calendar=hot)
    assert (
        line_for(warm, "nutrl").reasoning.forecast_over_cover
        > line_for(plain, "nutrl").reasoning.forecast_over_cover
    )


# -- the reasoning record ----------------------------------------------------


def test_every_quantity_carries_a_machine_readable_reasoning_record(engine):
    order = engine.suggest_vendor("superior", at=SUNDAY_4PM, on_hand={"bud_light": 50})
    record = line_for(order, "bud_light").reasoning.to_dict()
    for field in (
        "units_sold_last_week", "days_of_cover", "forecast_over_cover", "safety_stock",
        "counted_on_hand", "post_cutoff_adjustment", "effective_on_hand",
        "already_on_order", "need_units", "pack_size", "order_packs", "delivery_plan",
    ):
        assert field in record
    assert record["units_sold_last_week"] > 0
    assert len(record["forecast"]["days"]) == order.plan.days_of_cover
    assert "sold" in line_for(order, "bud_light").reasoning.one_liner()


def test_overrides_are_kept_and_recorded(engine):
    order = engine.suggest_vendor("superior", at=SUNDAY_4PM, overrides={"bud_light": 2})
    line = line_for(order, "bud_light")
    assert line.override_packs == 2
    assert line.final_packs == 2
    assert line.order_packs != 2  # the suggestion is preserved alongside the override


# -- vendor rules ------------------------------------------------------------


def test_arena_output_is_an_email_and_nothing_else(engine, catalog):
    order = engine.suggest_vendor("arena", at=SUNDAY_4PM)
    output = render_order(order)
    assert output.channel == "email"
    assert output.recipient == "arenaliquor@gmail.com"
    assert "email only" in output.body.lower()
    assert "Gursev" not in output.body
    assert emergency_contact(catalog.vendor("arena")).name == "Gursev"


def test_oyo_routes_through_arena_and_hides_the_direct_contact(engine):
    order = engine.suggest_vendor("oyo", at=SUNDAY_4PM)
    assert order.plan.vendor_key == "arena"          # planned against Arena's window
    assert any("routes through" in note for note in order.notes)
    hidden = render_order(order).body
    assert "(000) 000-0005" not in hidden
    unlocked = render_order(order, arena_out_of_stock=True).body
    assert "(000) 000-0005" in unlocked


def test_rotating_lines_get_a_style_and_count_never_a_sku(engine):
    order = engine.suggest_vendor("sixth_city", at=SUNDAY_4PM)
    assert order.lines == []
    assert len(order.style_recommendations) == 1
    recommendation = order.style_recommendations[0]
    assert recommendation.unit == "1/6 bbl"
    assert "Jenna" in recommendation.ask
    assert "sours and pale ales" in recommendation.styles
    assert recommendation.reasoning  # the reasoning survives even without a SKU
    assert "Rotating 1/6 bbl" not in render_order(order).body


def test_southern_glazers_offers_the_followup_only_when_tuesday_will_not_cover(engine, catalog):
    """The catalog caps Espolon at 6 bottles a delivery, so a big week goes short."""
    covered = engine.suggest_vendor("southern_glazers", at=SUNDAY_4PM)
    assert covered.follow_up_offer["offered"] is False

    calendar = {
        day: DayContext(day=day, events=["osu_home_football"])
        for day in [date(2026, 9, 1) + __import__("datetime").timedelta(days=n) for n in range(8)]
    }
    stretched = engine.suggest_vendor("southern_glazers", at=SUNDAY_4PM, calendar=calendar)
    offer = stretched.follow_up_offer
    assert offer["offered"] is True
    assert offer["confirm_with"] == "Bethany"
    assert "not guaranteed" in offer["flag"]
    assert offer["shortfalls"][0]["product"] == "espolon_blanco_750"


def test_superior_recommends_its_second_window_when_that_shrinks_the_order(engine):
    order = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    recommendation = order.window_recommendation
    assert recommendation["sunday_only_days_of_cover"] == 7
    assert recommendation["sunday_plus_thursday_days_of_cover"] == 4
    assert recommendation["sunday_plus_thursday_units"] < recommendation["sunday_only_units"]
    assert recommendation["recommend_second_window"] is True


def test_keg_vendors_require_an_empty_keg_return(engine):
    order = engine.suggest_vendor("superior", at=SUNDAY_4PM)
    assert order.to_dict()["empty_keg_return_required"] is True
    assert any("Empty keg return" in note for note in order.notes)


def test_heidelberg_delivery_note_rides_along(engine):
    order = engine.suggest_vendor("heidelberg", at=SUNDAY_4PM)
    assert any("hallway behind bar" in note for note in order.notes)


def test_a_vendor_with_no_assigned_products_says_so(catalog, history_depletion):
    for key in list(catalog.products):
        if catalog.products[key].vendor == "columbus_distributing":
            catalog.products[key] = catalog.products[key].__class__(
                **{**catalog.products[key].__dict__, "vendor": None}
            )
    order = OrderEngine(catalog, history_depletion).suggest_vendor(
        "columbus_distributing", at=SUNDAY_4PM
    )
    assert any("No products in the catalog" in warning for warning in order.warnings)


def test_suggest_all_skips_vendors_with_no_window(engine, catalog):
    orders = engine.suggest_all(at=SUNDAY_4PM)
    keys = {order.vendor.key for order in orders}
    assert "superior" in keys
    assert "oyo" in keys  # routed through Arena rather than skipped
