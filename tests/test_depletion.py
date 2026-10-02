"""Depletion math: pours, kegs, bottle service, comps, voids, unmapped rows."""

from __future__ import annotations

from datetime import date

import pytest

from thbev.depletion import DepletionEngine, packs_for_units
from thbev.ingest import parse_item_selection_details, parse_pmix
from thbev.models import ItemKey, SalesRow

LOCATION = "Townhall - Short North"


def row(item, *, category=None, menu=None, group=None, qty=1.0, **kwargs):
    return SalesRow(
        key=ItemKey(category, menu, group, item), qty=qty, source="test", **kwargs
    )


@pytest.fixture
def engine(catalog):
    return DepletionEngine(catalog)


# -- pours -------------------------------------------------------------------


def test_pour_defaults_to_single_when_no_modifier(engine, catalog):
    result = engine.deplete([row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila")])
    line = result.lines[0]
    assert line.pour_name == "single"
    assert line.oz == pytest.approx(1.5)
    assert result.counters["pour_defaulted"] == 1


def test_double_pour_depletes_twice_a_single(engine):
    single = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", modifiers=("Single",))]
    )
    double = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", modifiers=("Double",))]
    )
    rocks = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", modifiers=("Rocks",))]
    )
    assert single.lines[0].oz == pytest.approx(1.5)
    assert rocks.lines[0].oz == pytest.approx(2.5)
    assert double.lines[0].oz == pytest.approx(3.0)
    assert double.lines[0].units == pytest.approx(2 * single.lines[0].units)


def test_spirit_bottles_use_the_overpour_adjusted_yield(engine, catalog):
    """750ml = 25.36 oz theoretical; a 5% overpour makes it 24.15 usable."""
    result = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", qty=17)]
    )
    expected = (17 * 1.5) / (25.36 / 1.05)
    assert result.lines[0].units == pytest.approx(expected)
    assert result.lines[0].units > (17 * 1.5) / 25.36  # overpour costs more bottle


def test_unclassified_modifier_goes_to_the_unmapped_queue(engine):
    result = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", modifiers=("Extra Dirty",))]
    )
    assert result.counters["unmapped_modifiers"] == 1
    assert result.unmapped[0].qty == 1.0


def test_product_modifier_adds_its_own_depletion(engine):
    result = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", modifiers=("Add Red Bull",))]
    )
    products = {line.product_key for line in result.lines}
    assert products == {"espolon_blanco_750", "red_bull"}


# -- bottle service ----------------------------------------------------------


def test_bottle_service_depletes_a_whole_bottle_not_a_pour(engine):
    """The single most dangerous item type in the model."""
    pour = engine.deplete(
        [row("Espolon Blanco", category="Liquor", menu="LIQUOR", group="Tequila", qty=2)]
    )
    bottles = engine.deplete(
        [row("Espolon Blanco", category="Bottle Service", menu="BOTTLE SERVICE",
             group="Tequila Bottles", qty=2)]
    )
    spirit_line = next(l for l in bottles.lines if l.product_key == "espolon_bottle_service")
    assert spirit_line.units == 2.0
    assert spirit_line.units > 15 * pour.lines[0].units  # order-of-magnitude difference


def test_bottle_service_carries_its_bundled_mixers(engine):
    result = engine.deplete(
        [row("Espolon Blanco", category="Bottle Service", menu="BOTTLE SERVICE",
             group="Tequila Bottles", qty=3)]
    )
    mixer = next(l for l in result.lines if l.product_key == "red_bull")
    assert mixer.units == 12  # 4 per bottle x 3 bottles
    assert mixer.bottle_service is True


def test_bottle_service_is_flagged_for_baseline_exclusion(engine):
    result = engine.deplete(
        [row("Espolon Blanco", category="Bottle Service", menu="BOTTLE SERVICE",
             group="Tequila Bottles", qty=1)]
    )
    assert all(line.bottle_service for line in result.lines)
    assert "espolon_bottle_service" in result.bottle_service_units
    assert "espolon_bottle_service" not in result.units_by_product(include_bottle_service=False)


# -- draft, wine, recipes ----------------------------------------------------


def test_draft_uses_usable_keg_yield_without_double_counting_loss(engine, catalog):
    """1/2 bbl usable yield is 1,880 oz; the 5% loss is already in that number."""
    result = engine.deplete([row("House IPA Pint", qty=117)])
    line = result.lines[0]
    assert line.oz == pytest.approx(117 * 16)
    assert line.units == pytest.approx(117 * 16 / 1880)
    assert line.units == pytest.approx(0.9957, abs=1e-3)  # ~117 pints to a half barrel


def test_sixth_barrel_yield_is_about_39_pints(engine):
    """1/6 bbl usable yield is 627 oz, about 39 pints."""
    result = engine.deplete([row("Rotating Draft Pint", qty=39)])
    assert result.lines[0].units == pytest.approx(39 * 16 / 627)
    assert result.lines[0].units == pytest.approx(0.995, abs=1e-2)


def test_wine_by_the_glass_yields_five_glasses_a_bottle(engine):
    result = engine.deplete([row("House Chardonnay Glass", qty=5)])
    assert result.lines[0].oz == pytest.approx(25.0)
    assert result.lines[0].units == pytest.approx(25.0 / (25.36 / 1.05))


def test_cocktail_recipe_depletes_every_ingredient(engine):
    result = engine.deplete([row("PassionPunch Margarita", menu="COCKTAIL", qty=34)])
    by_product = {line.product_key: line for line in result.lines}
    assert set(by_product) == {"espolon_blanco_750", "chinola"}
    assert by_product["espolon_blanco_750"].oz == pytest.approx(34 * 1.5)
    assert by_product["chinola"].oz == pytest.approx(34 * 0.5)
    assert all(line.via == "recipe:passionpunch_margarita" for line in result.lines)


def test_prep_ingredient_cannot_be_sold_directly(catalog):
    """Chinola has no POS line of its own; a direct mapping is a catalog error."""
    from thbev.catalog.models import Mapping, MappingKey

    catalog.mappings.append(
        Mapping(key=MappingKey(menu_item="Chinola Shot"), product="chinola")
    )
    result = DepletionEngine(catalog).deplete([row("Chinola Shot", qty=5)])
    assert not result.lines
    assert result.counters["conversion_errors"] == 1
    assert "prep_ingredient" in result.unmapped[0].reason
    assert result.unmapped[0].qty == 5


# -- voids, comps, unmapped --------------------------------------------------


def test_voids_are_excluded_and_comps_are_counted_but_flagged(engine, fixtures_dir):
    parsed = parse_item_selection_details(
        fixtures_dir / "item_selection_details_with_mods.csv", location=LOCATION
    )
    result = engine.deplete(parsed.rows)
    bud = result.units_by_product()["bud_light"]
    assert bud == 2  # only the comped pair; the 4 voided bottles never arrive
    assert result.comped_units["bud_light"] == 2
    assert result.counters["comped_lines"] == 1


def test_unmapped_rows_keep_their_quantities(engine, fixtures_dir):
    parsed = parse_item_selection_details(
        fixtures_dir / "item_selection_details.csv", location=LOCATION
    )
    result = engine.deplete(parsed.rows)
    mystery = [u for u in result.unmapped if u.key.menu_item == "Mystery Shot"]
    assert mystery and mystery[0].qty == 8
    assert "no mapping" in mystery[0].reason


def test_business_dates_survive_into_depletion(engine, fixtures_dir):
    parsed = parse_item_selection_details(
        fixtures_dir / "item_selection_details.csv", location=LOCATION
    )
    result = engine.deplete(parsed.rows)
    daily = result.daily_units()
    # 12 at 21:00 plus 5 at 01:30 the next morning both land on Sunday.
    assert daily[("bud_light", date(2026, 8, 30))] == 17
    assert daily[("bud_light", date(2026, 8, 31))] == 1


def test_pmix_and_csv_agree_on_a_shared_item(catalog, fixtures_dir):
    """PMIX is the cross-check on totals; both shapes must map the same way."""
    engine = DepletionEngine(catalog)
    pmix = engine.deplete(parse_pmix(fixtures_dir / "pmix_full.xlsx").rows)
    assert pmix.units_by_product()["bud_light"] == 187
    assert pmix.units_by_product()["espolon_bottle_service"] == 2


# -- rounding ----------------------------------------------------------------


@pytest.mark.parametrize(
    "units, pack, expected",
    [
        (0, 24, 0),
        (-5, 24, 0),
        (1, 24, 1),
        (24, 24, 1),
        (25, 24, 2),
        (47.9, 24, 2),
        (48.0000000001, 24, 2),  # float noise must not buy an extra case
        (13, 6, 3),
    ],
)
def test_pack_rounding_always_rounds_up(units, pack, expected):
    assert packs_for_units(units, pack) == expected


def test_pack_rounding_rejects_bad_pack_size():
    with pytest.raises(ValueError):
        packs_for_units(10, 0)
