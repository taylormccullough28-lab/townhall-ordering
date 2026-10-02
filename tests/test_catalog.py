"""Catalog loading and composite-key mapping resolution."""

from __future__ import annotations

from datetime import time

import pytest
import yaml

from thbev.catalog import ConversionType, load_catalog
from thbev.catalog.loader import CatalogError


def test_seed_catalog_loads_and_validates(seed_catalog):
    assert seed_catalog.vendors["arena"].rules.email_only
    assert seed_catalog.vendors["oyo"].rules.route_through == "arena"
    assert seed_catalog.vendors["sixth_city"].rules.style_only
    assert seed_catalog.validate() == []


def test_seed_catalog_has_a_vendor_for_every_product(seed_catalog):
    """Gap 3 of CATALOG-COMPLETENESS.md is closed.

    Every product used to carry ``vendor: null`` because the product-to-distributor
    map lived in TH_ORDER_GUIDE.docx, which is not in this repo. The MarginEdge
    vendor-item catalog (pulled 2026-09-28, indexed in vendor_items.yaml) supplies
    it, so nothing is unassigned and nothing is left at ``unconfirmed``.
    """
    assert seed_catalog.unassigned_products() == []
    assert not [
        p.key for p in seed_catalog.products.values()
        if p.vendor_confidence == "unconfirmed"
    ]

    # The ones the PRD states outright keep the stronger "confirmed" label.
    assert seed_catalog.product("oyo_vodka_750").vendor == "arena"
    assert seed_catalog.product("oyo_vodka_750").vendor_confidence == "confirmed"
    assert seed_catalog.product("rotating_sixth_bbl_sixth_city").vendor == "sixth_city"

    # The ones MarginEdge supplied say so, and say which distributor.
    bud = seed_catalog.product("bud_light")
    assert bud.vendor == "columbus_distributing"
    assert bud.vendor_confidence == "marginedge"
    assert seed_catalog.product("suncruiser").vendor == "superior"
    assert seed_catalog.product("red_bull").vendor == "southern_glazers"
    assert seed_catalog.product("chinola").vendor == "heidelberg"


def test_dual_sourced_products_record_the_second_distributor(seed_catalog):
    """Real dual-sourcing is advisory, never a second order.

    The catalog models one vendor per product. Where MarginEdge shows a product
    stocked by more than one distributor, the extra ones go in ``alt_vendors`` so
    the fact is not lost, but ``vendor`` stays single and is the distributor the
    invoices show actually being used.
    """
    red_bull = seed_catalog.product("red_bull")
    assert red_bull.vendor == "southern_glazers"
    assert set(red_bull.alt_vendors) == {"arena", "columbus_distributing"}

    # Pamplemousse: Cavalier does carry it (item 12942), contrary to the
    # "Arena only" note, but Arena is the vendor the invoices use.
    pamp = seed_catalog.product("pamplemousse_750")
    assert pamp.vendor == "arena"
    assert pamp.alt_vendors == ("cavalier",)

    # A product is never listed as its own alternate, and every alternate is a
    # vendor the catalog actually knows how to order from.
    for product in seed_catalog.products.values():
        assert product.vendor not in product.alt_vendors
        for alt in product.alt_vendors:
            assert alt in seed_catalog.vendors


def test_composite_key_separates_same_named_items(catalog):
    """One name, two categories, two menus, two entirely different conversions."""
    pour = catalog.resolve(("liquor", "liquor", "tequila", "espolon blanco")).mapping
    bottle = catalog.resolve(
        ("bottle service", "bottle service", "tequila bottles", "espolon blanco")
    ).mapping
    assert pour.product == "espolon_blanco_750"
    assert bottle.product == "espolon_bottle_service"
    assert bottle.bottle_service is True


def test_blank_category_still_resolves_on_menu_structure(catalog):
    """PMIX exports with no Sales Category column must still map."""
    resolved = catalog.resolve(("", "liquor", "tequila", "espolon blanco")).mapping
    assert resolved.product == "espolon_blanco_750"
    bacardi = catalog.resolve(("", "liquor", "rum", "bacardi fb")).mapping
    assert bacardi.product == "bacardi_750"


def test_most_specific_mapping_wins(catalog):
    """A four-part match beats a three-part one; never the other way round."""
    resolved = catalog.resolve(("liquor", "liquor", "tequila", "espolon blanco"))
    assert resolved.mapping.key.specificity == 4


def test_unmapped_key_is_reported_not_guessed(catalog):
    resolution = catalog.resolve(("liquor", "liquor", "shots", "mystery shot"))
    assert resolution.mapping is None
    assert "no mapping" in resolution.reason


def test_ambiguous_mappings_are_refused(tmp_path, catalog):
    """Two equally specific mappings is a catalog bug, not a coin flip."""
    directory = tmp_path / "catalog"
    directory.mkdir()
    from tests.conftest import FIXTURES

    for name in ("vendors.yaml", "products.yaml", "config.yaml"):
        (directory / name).write_text(
            (FIXTURES / "catalog" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "mappings.yaml").write_text(
        yaml.safe_dump(
            {
                "mappings": [
                    {"key": {"menu": "LIQUOR", "menu_item": "Bud Light"}, "product": "bud_light"},
                    {"key": {"sales_category": "Liquor", "menu_item": "Bud Light"}, "product": "nutrl"},
                ]
            }
        ),
        encoding="utf-8",
    )
    conflicted = load_catalog(directory)
    resolution = conflicted.resolve(("liquor", "liquor", "domestics", "bud light"))
    assert resolution.mapping is None
    assert "ambiguous" in resolution.reason
    assert len(resolution.conflicts) == 2


def test_catalog_validation_catches_dangling_references(tmp_path):
    from tests.conftest import FIXTURES

    directory = tmp_path / "catalog"
    directory.mkdir()
    for name in ("vendors.yaml", "products.yaml", "config.yaml"):
        (directory / name).write_text(
            (FIXTURES / "catalog" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "mappings.yaml").write_text(
        yaml.safe_dump({"mappings": [{"key": {"menu_item": "X"}, "product": "does_not_exist"}]}),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError) as excinfo:
        load_catalog(directory)
    assert "does_not_exist" in str(excinfo.value)


def test_missing_catalog_file_raises(tmp_path):
    with pytest.raises(CatalogError):
        load_catalog(tmp_path)


def test_modifier_classification(catalog):
    assert catalog.resolve_modifier("Double").pour == "double"
    assert catalog.resolve_modifier("  double ").pour == "double"
    assert catalog.resolve_modifier("Add Red Bull").kind == "product"
    assert catalog.resolve_modifier("Extra Dirty") is None


def test_pour_sizes_are_the_confirmed_house_pours(seed_catalog):
    pours = seed_catalog.config.pours
    assert (pours.single, pours.rocks, pours.double) == (1.5, 2.5, 3.0)
    assert pours.default == "single"
    with pytest.raises(KeyError):
        pours.size_for("triple")


def test_effective_yield_applies_overpour(seed_catalog):
    config = seed_catalog.config
    assert config.overpour_factor == 0.05
    assert config.effective_yield_oz(25.36) == pytest.approx(25.36 / 1.05)


def test_prep_ingredients_are_indirect_only(seed_catalog):
    assert seed_catalog.product("chinola").conversion is ConversionType.PREP_INGREDIENT


class TestNamedSkusAndSeasonalProducts:
    """Cavalier is style-only, but carries specific products too.

    A named SKU must survive the rotating-line collapse, or the manager never
    sees the product on the order sheet.
    """

    def test_named_sku_and_alt_vendors_load(self):
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        bumble = catalog.products["fat_heads_bumble_berry"]
        assert bumble.vendor == "cavalier"
        assert bumble.named_sku is True
        assert bumble.keg_size == "half_barrel"

        # Pamplemousse is a 750ml liqueur ordered from Arena. MarginEdge shows
        # Cavalier stocks it too (item 12942), so Cavalier is an alt_vendor - but
        # it must not become Cavalier's product, or the rotating-line collapse
        # would swallow a named liqueur into a keg style-and-count.
        pamp = catalog.products["pamplemousse_750"]
        assert pamp.vendor == "arena"
        assert pamp.unit_size_oz == 25.36
        assert pamp.alt_vendors == ("cavalier",)
        assert "pamplemousse" not in {
            k for k, p in catalog.products.items() if p.vendor == "cavalier"
        }

    def test_superior_second_window_is_wednesday(self):
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        keys = {w.key for w in catalog.vendors["superior"].windows}
        assert "superior_wednesday" in keys
        assert "superior_thursday" not in keys
        wed = next(w for w in catalog.vendors["superior"].windows if w.key == "superior_wednesday")
        assert wed.order_weekday == 2          # Wednesday
        assert wed.delivery_weekday == 4       # Friday
        assert str(wed.order_time).startswith("19:00")


class TestStapleKegs:
    """The thirteen keg lines that repeated in 2026-08-28..09-28.

    A staple is a keg invoiced in two or more separate orders in that window.
    Everything else on tap was a one-off, which is the rotating program. The
    distinction matters because a rotating keg must never teach the engine a
    year-round baseline.
    """

    def test_every_staple_keg_loads_with_a_vendor_and_a_yield(self):
        from thbev.catalog.loader import load_catalog
        from thbev.depletion.engine import DepletionEngine

        catalog = load_catalog()
        # (key, vendor, keg_size, usable oz)
        expected = [
            ("downeast_original_keg", "superior", "half_barrel", 1880),
            ("bellafina_secco_keg", "heidelberg", "sixth_barrel", 627),
            ("garage_lime_keg", "superior", "half_barrel", 1880),
            ("busch_light_keg", "columbus_distributing", "half_barrel", 1880),
            ("cbc_bodhi_keg", "superior", "fifty_liter", 1603),
            ("miller_high_life_keg", "superior", "half_barrel", 1880),
            ("golden_road_mango_keg", "columbus_distributing", "half_barrel", 1880),
            ("cincy_light_keg", "superior", "half_barrel", 1880),
            ("hazy_little_thing_keg", "superior", "half_barrel", 1880),
            ("dogfish_30_minute_keg", "superior", "half_barrel", 1880),
            ("elvis_juice_keg", "superior", "half_barrel", 1880),
            ("real_american_keg", "heidelberg", "half_barrel", 1880),
        ]
        engine = DepletionEngine(catalog)
        for key, vendor, keg_size, usable_oz in expected:
            product = catalog.products[key]
            assert product.vendor == vendor, key
            assert product.keg_size == keg_size, key
            # A named SKU, so it survives the rotating-line collapse on a
            # style-only vendor and still reaches the order sheet by name.
            assert product.named_sku is True, key
            assert engine.keg_yield_oz(product) == usable_oz, key

    def test_fifty_litre_and_quarter_barrel_have_yields(self):
        """CBC Bodhi ships 50L; before this the engine could not size it."""
        from thbev.catalog.loader import load_catalog

        yields = load_catalog().config.yields
        # Nominal volume less ~5% foam and line loss, same basis as the others.
        assert yields.fifty_liter_oz == 1603.0
        assert yields.quarter_barrel_oz == 941.0
        assert yields.twenty_liter_oz == 641.0
        # A 50L keg sits between a 1/6 and a 1/2 barrel.
        assert yields.sixth_barrel_oz < yields.fifty_liter_oz < yields.half_barrel_oz

    def test_lucky_one_lemonade_is_in_the_catalog(self):
        """Missing entirely until the operator flagged it on 2026-09-29."""
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        original = catalog.products["lucky_one_original_lemonade"]
        assert original.vendor == "southern_glazers"
        assert original.pack_size == 24
        assert original.order_critical is True
        # The variety pack is carried but was not purchased in the sampled
        # window, so it has no baseline and must not be order_critical.
        variety = catalog.products["lucky_one_variety_lemonade"]
        assert variety.vendor == "southern_glazers"
        assert variety.order_critical is False


class TestHighVolumeVendorWindows:
    """Hillcrest and Amazon were the last two vendors with no window at all.

    They are also the largest by spend and by order count respectively, so the
    gap mattered more than for anyone else. The two were solved differently
    because they are different kinds of problem: Hillcrest has a real schedule
    that had simply never been written down, while Amazon has no vendor-imposed
    cutoff to discover, so its window is a policy choice.
    """

    def test_hillcrest_has_three_windows_across_two_accounts(self):
        from thbev.catalog.loader import load_catalog

        vendor = load_catalog().vendor("hillcrest")
        windows = {w.key: w for w in vendor.windows}
        assert set(windows) == {
            "hillcrest_food_sunday",
            "hillcrest_paper_monday",
            "hillcrest_both_thursday",
        }
        # Account 71357 (food) lands Monday; 71361 (paper) lands Tuesday; the
        # Thursday cutoff serves both and carries the Friday delivery, which is
        # over half the quarter's spend.
        assert windows["hillcrest_food_sunday"].delivery_weekday == 0
        assert windows["hillcrest_paper_monday"].delivery_weekday == 1
        assert windows["hillcrest_both_thursday"].delivery_weekday == 4
        # Cutoff confirmed by the operator 2026-09-29: 16:00 on every window,
        # both accounts. Nothing here is pending an outside answer any more.
        assert all(w.order_time.strftime("%H:%M") == "16:00" for w in vendor.windows)
        assert not any(w.requires_confirmation for w in vendor.windows)

    def test_amazon_windows_are_a_batching_policy_not_a_vendor_cutoff(self):
        from thbev.catalog.loader import load_catalog

        vendor = load_catalog().vendor("amazon")
        windows = {w.key: w for w in vendor.windows}
        assert set(windows) == {"amazon_monday_batch", "amazon_thursday_batch"}
        # Monday and Thursday were already Amazon's two heaviest days (44 and 38
        # of 195 orders), so the policy formalizes existing behaviour.
        assert windows["amazon_monday_batch"].order_weekday == 0
        assert windows["amazon_thursday_batch"].order_weekday == 3
        # The second batch is skippable when Monday covered the week.
        assert windows["amazon_thursday_batch"].optional is True
        # There is no rep to confirm a cutoff with, so confirmation is not
        # pending on anyone outside the building.
        assert not any(w.requires_confirmation for w in vendor.windows)

    def test_only_two_vendors_are_left_without_a_window(self):
        """Two blanks, for two different reasons, and neither is an oversight.

        OYO routes through Arena, so it has no cutoff of its own to record.
        Buckeye's delivery day is unambiguous - Monday, 12 of 17 invoices - but
        nobody has ever recorded the cutoff, and a window cannot be written
        without one. Inventing a plausible time would have the engine hand a
        manager a deadline that may not exist, which is worse than a blank.

        This assertion is the outstanding-work list. A third key appearing here
        means a vendor lost its window; buckeye disappearing means somebody
        finally asked the rep.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        windowless = sorted(
            key for key, vendor in catalog.vendors.items() if not vendor.windows
        )
        assert windowless == ["buckeye", "oyo"]

    def test_buckeye_is_in_the_catalog_at_all(self):
        """Buckeye was absent until 2026-09-29 despite outspending four vendors
        that were present. It supplies the draft gas, so an absent vendor is an
        unordered CO2 cylinder.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        assert "buckeye" in catalog.vendors
        assert catalog.vendors["buckeye"].name == "Buckeye Beverage"

    def test_heidelberg_delivers_thursday_not_tuesday(self):
        """Heidelberg moved Tuesday -> Thursday on 2026-09-01.

        Over the full quarter the invoices split 19 Tuesday / 16 Thursday, which
        reads as a two-day-a-week vendor. It is not: every Tuesday predates
        2026-09-01 and every invoice after it is a Thursday. The window must
        follow the current regime, not the quarter's average.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        windows = catalog.vendors["heidelberg"].windows
        assert len(windows) == 1
        window = windows[0]
        assert window.delivery_weekday == 3  # Thursday
        assert window.order_weekday == 2  # Wednesday
        assert window.order_time == time(17, 0)


class TestHartzlerIsTwoItems:
    """Hartzler supplies whole milk and half & half. Nothing else.

    Heavy cream, butter, cream cheese and sour cream were attributed here off a
    MarginEdge purchase report with no vendor column. The rates in that report
    were real; the vendor was inferred, and wrong. With a five-day lead, an item
    ordered here in error is not recoverable for a week, so the scope is pinned
    by a test rather than left to a comment.
    """

    def test_hartzler_supplies_exactly_two_products(self):
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        hartzler = sorted(
            key for key, p in catalog.products.items() if p.vendor == "hartzler"
        )
        assert hartzler == ["half_and_half", "milk_whole"]

    def test_the_misattributed_dairy_is_not_on_hartzler(self):
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        for key, product in catalog.products.items():
            if product.vendor != "hartzler":
                continue
            name = product.name.lower()
            for wrong in ("heavy cream", "butter", "cream cheese", "sour cream"):
                assert wrong not in name, f"{key} is not a Hartzler item"

    def test_both_items_order_in_cases(self):
        """The order is written in cases; gallons are how it gets miscounted."""
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        for key in ("milk_whole", "half_and_half"):
            product = catalog.products[key]
            assert product.unit_label == "case"
            assert product.order_critical is True


class TestRotatingKegVendors:
    """Sixth City and Cavalier, the two vendors the guide knew least about.

    Both are ordered by reading styles off a rep's availability list, so the
    catalog's job here is not to name SKUs - it is to carry the two facts that
    conversation never covers: which day the kegs actually land, and what a keg
    is allowed to cost.
    """

    def test_sixth_city_delivers_wednesday_not_tuesday(self):
        """11 of 11 invoices, 2026-06-24..09-16, landed Wednesday.

        vendors.yaml and test_end_to_end both carried Tuesday until 2026-10-01
        while the PRD appendix already said Wednesday. Two of the three sources
        agreed with each other and were wrong; the invoices decided it. A
        Tuesday here means the order is placed believing there is a day of cover
        that does not exist.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        window = catalog.vendor("sixth_city").window("sixth_city_monday")
        assert window.delivery_weekday == 2  # Wednesday
        assert window.lead_days == 2

    def test_both_rotating_vendors_carry_a_pour_cost_ceiling(self):
        """A style-and-count order has no natural place to notice price.

        Across the quarter a 1/6 bbl ran $49.99 to $224.99 - $1.28 to $5.74 a
        pour - and nothing in the ordering flow mentioned cost, because the brief
        is written in styles. The ceiling is the only guard against agreeing to a
        $5.74 pour by saying yes to "something pumpkin".

        The figure was $3.00 for one commit, picked near the observed median
        while the menu price was unknown. The operator confirmed $5.00 flat on
        2026-10-01, which makes $3.00 a 60% pour cost - the placeholder was
        twice the defensible number. It is now derived from the config rather
        than guessed, and the assertion below ties the two together so the
        vendor ceiling cannot drift away from the price it came from.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        config = catalog.config
        for key in ("sixth_city", "cavalier"):
            rules = catalog.vendor(key).rules
            assert rules.style_only is True
            assert rules.max_cost_per_pint == 1.50, key
            # $5.00 x 30% = $1.50 of keg per pour. Derived, not chosen.
            expected = config.draft_price * config.target_pour_cost
            assert rules.max_cost_per_pint == pytest.approx(expected), key

    def test_pour_cost_maths_matches_the_invoices(self):
        """Spot-check the config helpers against real 2026 keg prices.

        These four are the load-bearing cases: the keg that loses money, the one
        that only works because of its format, the median, and the one cheap
        enough to clear on a sixth barrel.
        """
        from thbev.catalog.loader import load_catalog

        config = load_catalog().config
        sixth, half = 627.0, 1880.0
        # Platform Pumpkin Kerfuffle, Cavalier 23422 - above 1.0 is a loss.
        assert config.pour_cost(224.99, sixth) == pytest.approx(1.148, abs=0.001)
        # 450 North Supersize Painkiller, Sixth City - also a loss.
        assert config.pour_cost(199.99, sixth) == pytest.approx(1.021, abs=0.001)
        # Fat Head's Bumble Berry. The same $169.99 in a sixth barrel would be
        # 87% - three times the pour cost for identical money, purely on format.
        assert config.pour_cost(169.99, half) == pytest.approx(0.289, abs=0.001)
        assert config.pour_cost(169.99, sixth) == pytest.approx(0.868, abs=0.001)
        # The median sixth barrel bought this quarter.
        assert config.pour_cost(109.99, sixth) == pytest.approx(0.561, abs=0.001)

    def test_the_sixth_barrel_ceiling_is_below_what_the_market_charges(self):
        """The finding that makes this a pricing problem, not a tuning one.

        At $5.00 / 16oz / 30% a sixth barrel may cost $58.78. Of 45 distinct
        rotating kegs bought in the quarter, exactly one was under that, and the
        median was $109.99. Loosening the target does not rescue it: even at 35%
        the ceiling is $68.58. This test exists so that if someone raises
        target_pour_cost to make the warnings go away, the gap is still visible.
        """
        from thbev.catalog.loader import load_catalog

        config = load_catalog().config
        sixth = 627.0
        assert config.max_keg_cost(sixth) == pytest.approx(58.78, abs=0.01)
        # The median sixth barrel actually bought, 2026-06-24..09-16.
        assert 109.99 > config.max_keg_cost(sixth)
        # A half barrel at the same target comfortably clears real prices.
        assert config.max_keg_cost(1880.0) == pytest.approx(176.25, abs=0.01)
        assert 169.99 < config.max_keg_cost(1880.0)

    def test_the_ceiling_actually_survives_the_loader(self):
        """Guards the bug this was written with.

        max_cost_per_pint sat in vendors.yaml for one commit while the loader
        ignored it, so the rule existed in the seed data and nowhere else. The
        loader builds VendorRules field by field, so any rules key it does not
        name is dropped in silence.
        """
        from thbev.catalog.models import VendorRules

        assert "max_cost_per_pint" in VendorRules.__dataclass_fields__
        assert VendorRules().max_cost_per_pint == 0.0

    def test_no_other_vendor_claims_a_pour_ceiling(self):
        """The ceiling belongs to style-ordered lines only.

        A vendor whose order names SKUs has a price on the sheet in front of
        you. Putting a ceiling on those would silently suppress a staple.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        capped = sorted(
            key
            for key, vendor in catalog.vendors.items()
            if vendor.rules.max_cost_per_pint
        )
        assert capped == ["cavalier", "sixth_city"]

    def test_cavalier_keeps_its_named_sku_despite_being_style_only(self):
        """Bumble Berry is 38% of the account - it must not collapse into a style.

        5 orders, 7 half-barrels, $1,189.93 over 2026-06-30..09-15. The guide
        called it an exception to Cavalier's "1/6 bbl only" rule; the quarter
        says it is the rule and the 1/6 rotation is the sideline.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        named = [
            key
            for key, p in catalog.products.items()
            if p.vendor == "cavalier" and getattr(p, "named_sku", False)
        ]
        assert named, "Cavalier must keep at least one named SKU"
        assert any("bumble" in catalog.products[k].name.lower() for k in named)

    def test_cavalier_carries_the_non_keg_items_too(self):
        """14% of the Cavalier account is not beer, and it was invisible.

        $429.84 of the 2026-06-30..09-15 quarter is cherries, rhubarb liqueur and
        prosecco. The guide collapsed this vendor to "rotating kegs, ask Dan",
        which left bar prep to memory on a vendor nobody thinks of as a prep
        supplier. style_only has to apply to the rotating portion of an account,
        never to the whole account.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        for key in ("amarena_cherries", "giffard_rhubarb_750",
                    "sun_goddess_prosecco_rose"):
            product = catalog.products[key]
            assert product.vendor == "cavalier", key
            # Each must survive the rotating-line collapse on its own.
            assert product.named_sku is True, key

    def test_the_amarena_cherries_are_order_critical(self):
        """Bought twice in the quarter, so it is a running line, not a one-off.

        It is also the one item here that stops a drink being made rather than
        merely narrowing the list.
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        assert catalog.products["amarena_cherries"].order_critical is True


class TestHartzlerHolidayDeadlines:
    """The dairy's 2026 holiday notice, received 2026-10-02.

    Hartzler is the longest lead in the building (Thursday 17:00 for Tuesday)
    and supplies two items the cafe cannot open without. Their notice says
    plainly "we will be unable to accept late orders", so a missed holiday
    cutoff is a week without milk rather than a late delivery. That is why
    these live as dated data rather than a note: a note does not fire on the
    day it matters.
    """

    def _rules(self):
        from thbev.catalog.loader import load_catalog

        return load_catalog().vendor("hartzler").rules

    def test_all_five_deadlines_load(self):
        rules = self._rules()
        assert len(rules.holiday_overrides) == 5
        # Every holiday deadline is 10:00, against a standing cutoff of 17:00.
        assert all(o.order_by.hour == 10 for o in rules.holiday_overrides)

    def test_the_three_wednesday_deadlines_are_the_dangerous_ones(self):
        """Three fall 31h before the normal cutoff; two fall 17h after it.

        The Friday pair is harmless - anyone keeping the Thursday 17:00 habit
        has already beaten them. The Wednesday trio is the whole risk, and the
        reason is structural: Hartzler's order day is Thursday, and
        Thanksgiving, Christmas Eve and New Year's Eve are all Thursdays.
        """
        from datetime import datetime, timedelta

        rules = self._rules()
        dangerous, harmless = [], []
        for override in rules.holiday_overrides:
            # The Tuesday delivery in that week, and the Thursday 17:00 before it.
            tuesday = override.delivery_week_start + timedelta(days=1)
            normal = datetime.combine(
                tuesday - timedelta(days=5), time(17, 0)
            )
            (dangerous if override.order_by < normal else harmless).append(override)

        assert len(dangerous) == 3
        assert {o.order_by.strftime("%a") for o in dangerous} == {"Wed"}
        assert {o.order_by.strftime("%a") for o in harmless} == {"Fri"}

    def test_every_closure_lands_on_the_normal_order_day_or_the_day_after(self):
        """Why the deadlines moved at all: the closures eat Thursday.

        All six closed days are Thursday/Friday pairs, and Thursday is the
        standing order day. If a future notice closes a Monday, nothing here
        would need to move - this assertion records that the 2026 pattern is a
        coincidence of the calendar, not a rule.
        """
        rules = self._rules()
        assert len(rules.closed_dates) == 6
        assert {d.weekday() for d in rules.closed_dates} == {3, 4}  # Thu, Fri

    def test_a_delivery_in_a_holiday_week_finds_its_override(self):
        from datetime import date, datetime

        rules = self._rules()
        # Tuesday 1 Dec 2026 is in the week after Thanksgiving.
        found = rules.override_for(date(2026, 12, 1))
        assert found is not None
        assert found.order_by == datetime(2026, 11, 25, 10, 0)
        # An ordinary week has no override and must fall back to the window.
        assert rules.override_for(date(2026, 10, 13)) is None

    def test_the_january_order_is_placed_in_the_previous_year(self):
        """The one most likely to be missed outright.

        The week of 4 Jan 2027 is ordered on 30 Dec 2026. Anything that reasons
        about "this month" or rolls over at year end will lose it.
        """
        from datetime import date

        rules = self._rules()
        january = rules.override_for(date(2027, 1, 5))
        assert january is not None
        assert january.order_by.year == 2026
        assert january.delivery_week_start.year == 2027

    def test_no_other_vendor_has_holiday_overrides_yet(self):
        """Only Hartzler sent a notice. The rest are still unknown, not clear.

        Holiday schedules exist for every vendor; we have one in writing. This
        records which, so an empty list is not mistaken for "business as usual".
        """
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        with_overrides = sorted(
            key
            for key, vendor in catalog.vendors.items()
            if vendor.rules.holiday_overrides
        )
        assert with_overrides == ["hartzler"]
