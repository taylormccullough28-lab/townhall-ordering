"""Tests for the MarginEdge Purchase Report parser.

The fixture reproduces the hazards observed in the real 2026-07-20..08-28
export: an unnamed GL-account column, accounting-negative credit lines,
unit-of-measure cells contaminated with product names, deposit lines that are
charges rather than products, and a second restaurant that must be filtered out.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thbev.ingest.purchase_report import (
    keg_deposit_balance,
    parse_purchase_report,
    parse_unit,
)
from thbev.models import Severity

FIXTURE = Path(__file__).parent / "fixtures" / "purchase_report_synthetic.csv"


@pytest.fixture
def result():
    return parse_purchase_report(FIXTURE, restaurant="TownHall - Columbus")


class TestParseUnit:
    @pytest.mark.parametrize(
        "raw,unit,oz,contaminated",
        [
            ("Bottle (750 Milliliters)", "Bottle", 25.36, False),
            ("Bottle (Liter)", "Bottle", 33.81, False),
            ("Keg (1/6BBL) 5.16GAL", "Keg", 660.48, False),
            ("Keg (1/2BBL) 15.5GAL", "Keg", 1984.0, False),
            ("Keg (1/4BBL) 7.75GAL", "Keg", 992.0, False),
            ("Can (12 Fluid Ounces)", "Can", 12.0, False),
            ("12oz (Bottle)", "Bottle", 12.0, False),
            ("OYO 750mL (Bottle)", "Bottle", 25.36, True),
            ("Michelob Ultra (Can)", "Can", None, True),
            ("Pound", "Pound", None, False),
        ],
    )
    def test_shapes(self, raw, unit, oz, contaminated):
        got_unit, got_oz, got_contaminated = parse_unit(raw)
        assert got_unit == unit
        assert got_contaminated is contaminated
        if oz is None:
            assert got_oz is None
        else:
            assert got_oz == pytest.approx(oz, abs=0.02)

    def test_outside_unit_noun_beats_parenthetical(self):
        """"Bottle (Liter)" is a litre bottle, not a unit called Liter."""
        assert parse_unit("Bottle (Liter)")[0] == "Bottle"

    def test_blank(self):
        assert parse_unit("") == (None, None, False)


class TestParsing:
    def test_filters_to_restaurant(self, result):
        assert {line.restaurant for line in result.lines} == {"TownHall - Columbus"}
        assert result.counters["rows_other_restaurant"] == 1

    def test_unnamed_gl_column_resolved(self, result):
        """The GL account has no header; it must still classify beverage."""
        titos = next(l for l in result.lines if l.product == "Titos Handmade Vodka")
        assert titos.gl_account == "COGS Liquor"
        assert titos.is_beverage

    def test_food_excluded_from_beverage(self, result):
        onions = next(l for l in result.lines if l.product == "Onions, Yellow")
        assert onions.gl_account == "COGS Food"
        assert not onions.is_beverage

    def test_deposits_separated_from_products(self, result):
        products = {line.product for line in result.lines}
        assert not any("Deposit" in p for p in products)
        assert len(result.deposits) == 4  # 3 keg + 1 bottle

    def test_accounting_negatives_stay_negative(self, result):
        """Credits are returns. Losing the sign loses the keg-credit signal."""
        ret = next(l for l in result.deposits if "At Return" in l.product)
        assert ret.units == -31
        assert ret.amount == -930.0

    def test_contamination_flagged(self, result):
        oyo = next(l for l in result.lines if l.product == "Vodka, OYO")
        assert oyo.unit_name_contaminated
        assert oyo.unit == "Bottle"

    def test_keg_volume_resolved(self, result):
        keg = next(l for l in result.lines if "Downeast" in l.product)
        assert keg.unit == "Keg"
        assert keg.unit_volume_oz == pytest.approx(1984.0)

    def test_weekly_rate(self, result):
        mich = next(l for l in result.lines if l.product.startswith("Michelob Ultra Pure"))
        assert mich.units == 2808
        assert mich.weekly_rate(5.714) == pytest.approx(491.4, abs=1.0)

    def test_missing_gl_column_refuses(self, tmp_path):
        """Without the GL column nothing can be classified; refuse, don't guess."""
        bad = tmp_path / "bad.csv"
        bad.write_text(
            "Restaurant,Product,Category,Report By,Purchased Units,Purchased Amount,Avg Cost\n"
            "TownHall - Columbus,Titos,COGS Liquor,Bottle,10,$190.00,$19.00\n"
        )
        res = parse_purchase_report(bad)
        assert not res.lines
        assert any(i.code == "missing_gl_column" and i.severity is Severity.ERROR for i in res.issues)


class TestKegDeposits:
    def test_balance(self, result):
        bal = keg_deposit_balance(result)
        assert bal["charged_units"] == 76
        assert bal["returned_units"] == 34
        assert bal["outstanding_units"] == 42
        assert bal["outstanding_amount"] == pytest.approx(1260.0)
        assert bal["return_rate"] == pytest.approx(34 / 76)

    def test_bottle_deposits_excluded_from_keg_balance(self, result):
        """Bottle deposits are a separate ledger; mixing them distorts keg capture."""
        assert keg_deposit_balance(result)["charged_units"] == 76
