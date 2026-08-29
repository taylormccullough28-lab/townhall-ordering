"""Shared test fixtures.

Every data file under ``tests/fixtures`` is synthetic; see the README there.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = Path(__file__).resolve().parent / "fixtures"

from thbev.catalog import load_catalog  # noqa: E402
from thbev.depletion import DepletionEngine  # noqa: E402
from thbev.ingest import parse_item_selection_details  # noqa: E402

LOCATION = "Townhall - Short North"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def seed_catalog():
    """The catalog that ships with the package."""
    return load_catalog()


@pytest.fixture
def catalog():
    """The synthetic test catalog, with vendors assigned to products."""
    return load_catalog(FIXTURES / "catalog")


@pytest.fixture
def history_rows():
    """Five weeks of timestamped sales ending Sunday 2026-08-30."""
    result = parse_item_selection_details(
        FIXTURES / "item_selection_history.csv", location=LOCATION, cutoff_hour=4
    )
    return result


@pytest.fixture
def history_depletion(catalog, history_rows):
    """Depletion for the five-week history."""
    return DepletionEngine(catalog).deplete(history_rows.rows)


@pytest.fixture
def sunday_cutoff() -> datetime:
    """Sunday 2026-08-30, 4:00 PM -- a manager counting before the 5-7 PM windows."""
    return datetime(2026, 8, 30, 16, 0)


@pytest.fixture
def last_business_day() -> date:
    return date(2026, 8, 30)
