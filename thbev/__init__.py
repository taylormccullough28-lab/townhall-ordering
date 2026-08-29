"""TownHall Columbus beverage ordering engine.

Ingest Toast sales exports, convert them to product depletion, forecast the week
ahead, and produce a per-vendor order sheet with a reasoning record behind every
quantity.

The sales input is behind :class:`thbev.sources.base.SalesSource`, so the
working file-upload path and any future API path are interchangeable.
"""

from .models import IngestResult, ItemKey, SalesRow, UnmappedRow
from .timeutil import business_day_of

__version__ = "0.1.0"

__all__ = [
    "IngestResult",
    "ItemKey",
    "SalesRow",
    "UnmappedRow",
    "business_day_of",
    "__version__",
]
