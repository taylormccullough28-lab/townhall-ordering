"""Catalog loading and composite-key mapping resolution."""

from __future__ import annotations

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
        # Delivery days are evidence; the cutoff times are placeholders. Every
        # window must say so, or the engine will quote a cover date off a guess.
        assert all(w.requires_confirmation for w in vendor.windows)

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

    def test_no_vendor_is_left_without_a_window_except_the_backup(self):
        """OYO is order-through-Arena-first, so it is the only blank left."""
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        windowless = sorted(
            key for key, vendor in catalog.vendors.items() if not vendor.windows
        )
        assert windowless == ["oyo"]


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
