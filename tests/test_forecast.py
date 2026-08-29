"""Baseline, multipliers, and the post-cutoff depletion adjustment."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from thbev.ordering import (
    BaselineModel,
    Buyout,
    DayContext,
    ForecastError,
    HourlyProfile,
    MultiplierEngine,
    PostCutoffUnavailable,
    Weather,
    forecast_product,
    project_sales,
    trimmed_mean,
)


# -- trimmed mean ------------------------------------------------------------


def test_trimmed_mean_drops_the_outlier_week():
    """One OSU Saturday must not drag a four-week Saturday mean up on its own."""
    assert trimmed_mean([10, 12, 11, 300]) == pytest.approx(11.5)
    assert trimmed_mean([10, 12, 11, 300], trim="none") == pytest.approx(83.25)


def test_trimmed_mean_needs_four_observations_to_trim():
    assert trimmed_mean([10, 12, 300]) == pytest.approx(107.333, abs=1e-3)
    assert trimmed_mean([]) == 0.0


def test_unknown_trim_strategy_raises():
    with pytest.raises(ValueError):
        trimmed_mean([1, 2, 3, 4], trim="winsorize")


# -- baseline ----------------------------------------------------------------


def test_baseline_counts_closed_days_as_zero_not_as_missing():
    """A slow SKU that sold on one Tuesday out of four averages 2.5, not 10."""
    days = [date(2026, 8, 4), date(2026, 8, 11), date(2026, 8, 18), date(2026, 8, 25)]
    model = BaselineModel({("slow", date(2026, 8, 25)): 10.0}, days, trim="none")
    assert model.baseline("slow", 1) == pytest.approx(2.5)


def test_baseline_uses_only_the_trailing_window():
    days = [date(2026, 7, 7), date(2026, 7, 14), date(2026, 7, 21), date(2026, 7, 28),
            date(2026, 8, 4)]
    units = {("x", day): 100.0 for day in days[:1]}
    units.update({("x", day): 10.0 for day in days[1:]})
    model = BaselineModel(units, days, weeks=4, trim="none")
    assert model.baseline("x", 1) == pytest.approx(10.0)  # the 100 week fell out


def test_baseline_from_real_history(history_depletion, catalog):
    model = BaselineModel(
        history_depletion.daily_units(include_bottle_service=False),
        sorted({day for _, day in history_depletion.daily_units()}),
        weeks=4,
        trim="high_low",
    )
    saturday = model.baseline("bud_light", 5)
    monday = model.baseline("bud_light", 0)
    assert saturday > monday * 2  # the fixture's Saturday is the big night
    assert model.weeks_of_history(5) == 4


# -- multipliers -------------------------------------------------------------


def test_osu_lifts_light_beer_more_than_everything_else(catalog):
    engine = MultiplierEngine(catalog.config)
    light = catalog.product("bud_light")
    spirits = catalog.product("espolon_blanco_750")
    context = DayContext(day=date(2026, 9, 5), events=["osu_home_football"])
    assert engine.for_day(light, context)[0].factor == pytest.approx(1.90)
    assert engine.for_day(spirits, context)[0].factor == pytest.approx(1.60)


def test_weather_multipliers_are_conditional(catalog):
    engine = MultiplierEngine(catalog.config)
    seltzer = catalog.product("nutrl")
    hot_sunny = DayContext(day=date(2026, 9, 5), weather=Weather(high_f=90, sunny=True))
    hot_cloudy = DayContext(day=date(2026, 9, 5), weather=Weather(high_f=90, sunny=False))
    cold = DayContext(day=date(2026, 12, 5), weather=Weather(high_f=30))
    assert engine.for_day(seltzer, hot_sunny)[0].factor == pytest.approx(1.20)
    assert engine.for_day(seltzer, hot_cloudy) == []
    assert engine.for_day(seltzer, cold)[0].factor == pytest.approx(0.85)


def test_multipliers_stack(catalog):
    engine = MultiplierEngine(catalog.config)
    context = DayContext(
        day=date(2026, 9, 5),
        events=["osu_home_football"],
        weather=Weather(high_f=90, sunny=True),
        promos={"bud_light": 1.1},
    )
    factors = [m.factor for m in engine.for_day(catalog.product("bud_light"), context)]
    assert sorted(factors) == pytest.approx(sorted([1.90, 1.20, 1.1]))


def test_unknown_event_is_refused(catalog):
    engine = MultiplierEngine(catalog.config)
    with pytest.raises(ForecastError):
        engine.for_day(catalog.product("bud_light"), DayContext(date(2026, 9, 5), events=["ufo"]))


def test_buyout_without_a_configured_rate_raises_rather_than_forecasting_zero(catalog):
    engine = MultiplierEngine(catalog.config)
    with pytest.raises(ForecastError) as excinfo:
        engine.buyout_units(catalog.product("bud_light"), Buyout(headcount=120))
    assert "buyout_per_head_units" in str(excinfo.value)


def test_buyout_overrides_the_baseline_when_a_rate_exists(catalog):
    catalog.config.buyout_per_head_units = {"light_beer": 1.5}
    model = BaselineModel({("bud_light", date(2026, 8, 24)): 40.0}, [date(2026, 8, 24)])
    forecast = forecast_product(
        catalog.product("bud_light"),
        [DayContext(day=date(2026, 8, 31), buyout=Buyout(headcount=100))],
        model,
        MultiplierEngine(catalog.config),
    )
    assert forecast.total == pytest.approx(150.0)
    assert forecast.days[0].overridden_by == "Private buyout"


def test_bottle_service_is_forecast_from_bookings_not_from_history(catalog):
    """Left in the trailing average, one buyout inflates a premium spirit for a month."""
    product = catalog.product("espolon_bottle_service")
    assert product.excluded_from_baseline
    model = BaselineModel({("espolon_bottle_service", date(2026, 8, 29)): 12.0}, [date(2026, 8, 29)])
    engine = MultiplierEngine(catalog.config)
    quiet = forecast_product(product, [DayContext(day=date(2026, 9, 5))], model, engine)
    booked = forecast_product(
        product,
        [DayContext(day=date(2026, 9, 5), promos={"espolon_bottle_service": 4})],
        model,
        engine,
    )
    assert quiet.total == 0.0          # nothing booked, not "12 like last week"
    assert booked.total == 4.0


# -- hourly profile and the post-cutoff adjustment ---------------------------


def test_hourly_profile_needs_timestamps(catalog, fixtures_dir):
    """PMIX has no time dimension; the adjustment must refuse, not guess."""
    from thbev.depletion import DepletionEngine
    from thbev.ingest import parse_pmix

    depletion = DepletionEngine(catalog).deplete(parse_pmix(fixtures_dir / "pmix_full.xlsx").rows)
    with pytest.raises(PostCutoffUnavailable) as excinfo:
        HourlyProfile.from_depletion(depletion, 4)
    assert "no time dimension" in str(excinfo.value)


def test_hourly_profile_puts_the_volume_at_night(history_depletion):
    profile = HourlyProfile.from_depletion(history_depletion, 4)
    # Nothing before 16:00 (slot 12) in the fixture's shape.
    assert profile.fraction_between(datetime(2026, 8, 30, 4, 0), datetime(2026, 8, 30, 16, 0)) == 0.0
    evening = profile.fraction_between(datetime(2026, 8, 30, 17, 0), datetime(2026, 8, 31, 4, 0))
    assert evening > 0.95  # the fixture bar does almost all its volume after 5 PM


def test_remaining_fraction_shrinks_as_the_night_goes_on(history_depletion):
    profile = HourlyProfile.from_depletion(history_depletion, 4)
    at_five = profile.remaining_fraction(datetime(2026, 8, 30, 17, 0))
    at_eleven = profile.remaining_fraction(datetime(2026, 8, 30, 23, 0))
    assert at_five > at_eleven > 0


def test_post_cutoff_projection_reduces_effective_on_hand(catalog, history_depletion):
    """Counting at 4pm Sunday overstates what Monday's truck lands against."""
    daily = history_depletion.daily_units(include_bottle_service=False)
    model = BaselineModel(daily, sorted({day for _, day in daily}), weeks=4)
    profile = HourlyProfile.from_depletion(history_depletion, 4)
    projection = project_sales(
        catalog.product("bud_light"),
        datetime(2026, 8, 30, 16, 0),   # count taken Sunday afternoon
        datetime(2026, 8, 31, 9, 0),    # Monday morning delivery
        model,
        MultiplierEngine(catalog.config),
        profile,
    )
    sunday_baseline = model.baseline("bud_light", 6)
    assert projection.units > 0
    # Almost the whole Sunday is still ahead at 4pm, and Monday has not started.
    assert projection.units == pytest.approx(sunday_baseline, rel=0.05)
    assert projection.detail[0]["day"] == "2026-08-30"


def test_post_cutoff_projection_applies_event_multipliers(catalog, history_depletion):
    daily = history_depletion.daily_units(include_bottle_service=False)
    model = BaselineModel(daily, sorted({day for _, day in daily}), weeks=4)
    profile = HourlyProfile.from_depletion(history_depletion, 4)
    plain = project_sales(
        catalog.product("bud_light"), datetime(2026, 8, 30, 16, 0),
        datetime(2026, 8, 31, 9, 0), model, MultiplierEngine(catalog.config), profile,
    )
    game_day = project_sales(
        catalog.product("bud_light"), datetime(2026, 8, 30, 16, 0),
        datetime(2026, 8, 31, 9, 0), model, MultiplierEngine(catalog.config), profile,
        contexts={date(2026, 8, 30): DayContext(date(2026, 8, 30), events=["osu_home_football"])},
    )
    assert game_day.units == pytest.approx(plain.units * 1.9)
