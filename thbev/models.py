"""Normalized data model shared by every sales source.

Anything a :class:`~thbev.sources.base.SalesSource` returns is expressed here,
so swapping a file upload for a future API is a config change rather than a
rewrite of the depletion and ordering engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Iterable

from .normalize import normalize_key


class Severity(str, Enum):
    """How much a reported ingest problem should worry the reader."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ItemKey:
    """The composite mapping key: Sales Category + Menu + Menu Group + Menu Item.

    Name-only matching is wrong for this data set -- the same item carries
    different Sales Categories on different menus -- so every catalog lookup
    goes through this four-part key. Any part may be None: PMIX ``Items``
    sheets carry no menu structure, and blank Sales Category occurs on genuine
    liquor SKUs.
    """

    sales_category: str | None
    menu: str | None
    menu_group: str | None
    menu_item: str | None

    @property
    def normalized(self) -> tuple[str, str, str, str]:
        """Case/punctuation-insensitive tuple used for catalog matching."""
        return (
            normalize_key(self.sales_category) if self.sales_category else "",
            normalize_key(self.menu) if self.menu else "",
            normalize_key(self.menu_group) if self.menu_group else "",
            normalize_key(self.menu_item) if self.menu_item else "",
        )

    def __str__(self) -> str:  # pragma: no cover - display only
        parts = [self.sales_category or "-", self.menu or "-", self.menu_group or "-", self.menu_item or "-"]
        return " | ".join(parts)


@dataclass
class SalesRow:
    """One normalized unit of sales.

    A PMIX row is an aggregate over the whole export range (``sold_at`` is
    None); an ItemSelectionDetails row is a single line item with a timestamp.
    Downstream code must check ``sold_at``/``business_date`` rather than assume
    a time dimension exists.
    """

    key: ItemKey
    qty: float
    source: str
    sold_at: datetime | None = None
    business_date: date | None = None
    location: str | None = None
    order_id: str | None = None
    net_price: float | None = None
    voided: bool = False
    comped: bool = False
    modifiers: tuple[str, ...] = ()
    row_number: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def has_time_dimension(self) -> bool:
        """True when this row can support post-cutoff hourly proration."""
        return self.sold_at is not None


@dataclass
class UnmappedRow:
    """A row that survived filtering but could not be turned into a SalesRow.

    Quantities are preserved so the caller can see the size of what it is not
    counting. Nothing is ever dropped silently.
    """

    reason: str
    qty: float | None
    source: str
    row_number: int | None = None
    key: ItemKey | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Issue:
    """A structural observation about a file: missing column, skipped sheet, filtered rows."""

    severity: Severity
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"[{self.severity.value}] {self.code}: {self.message}"


@dataclass
class IngestResult:
    """Everything one parse produced, including what it could not use."""

    rows: list[SalesRow] = field(default_factory=list)
    unmapped: list[UnmappedRow] = field(default_factory=list)
    voided: list[SalesRow] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    sheets_present: list[str] = field(default_factory=list)
    sheets_used: list[str] = field(default_factory=list)
    missing_columns: dict[str, list[str]] = field(default_factory=dict)
    source_files: list[str] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)

    def bump(self, name: str, amount: int = 1) -> None:
        """Increment a named counter (rollup rows skipped, voids excluded, ...)."""
        self.counters[name] = self.counters.get(name, 0) + amount

    def add_issue(
        self, severity: Severity, code: str, message: str, **context: Any
    ) -> None:
        """Record a structural observation."""
        self.issues.append(Issue(severity, code, message, context))

    def extend(self, other: "IngestResult") -> None:
        """Merge another result into this one (multi-file ingest)."""
        self.rows.extend(other.rows)
        self.unmapped.extend(other.unmapped)
        self.voided.extend(other.voided)
        self.issues.extend(other.issues)
        self.sheets_present.extend(other.sheets_present)
        self.sheets_used.extend(other.sheets_used)
        self.source_files.extend(other.source_files)
        for name, columns in other.missing_columns.items():
            self.missing_columns.setdefault(name, []).extend(columns)
        for name, value in other.counters.items():
            self.counters[name] = self.counters.get(name, 0) + value

    @property
    def total_qty(self) -> float:
        """Sum of quantities on usable rows -- the number that must not double-count."""
        return sum(row.qty for row in self.rows)

    @property
    def has_time_dimension(self) -> bool:
        """True when at least one row carries a timestamp."""
        return any(row.has_time_dimension for row in self.rows)

    def by_business_date(self) -> dict[date, list[SalesRow]]:
        """Group usable rows by business date, skipping undated (PMIX) rows."""
        grouped: dict[date, list[SalesRow]] = {}
        for row in self.rows:
            if row.business_date is None:
                continue
            grouped.setdefault(row.business_date, []).append(row)
        return grouped

    def summary(self) -> dict[str, Any]:
        """Machine-readable summary for the CLI and for logs."""
        return {
            "source_files": list(self.source_files),
            "rows": len(self.rows),
            "total_qty": self.total_qty,
            "unmapped_rows": len(self.unmapped),
            "unmapped_qty": sum(u.qty or 0.0 for u in self.unmapped),
            "voided_rows": len(self.voided),
            "sheets_present": list(self.sheets_present),
            "sheets_used": list(self.sheets_used),
            "missing_columns": dict(self.missing_columns),
            "counters": dict(self.counters),
            "issues": [
                {"severity": i.severity.value, "code": i.code, "message": i.message, **i.context}
                for i in self.issues
            ],
            "has_time_dimension": self.has_time_dimension,
        }


def filter_rows_to_range(
    rows: Iterable[SalesRow], start: date | None, end: date | None
) -> tuple[list[SalesRow], int]:
    """Filter rows to an inclusive business-date range.

    Undated rows (PMIX aggregates) are always kept -- the export range itself
    is the date filter for those files. Returns ``(kept, dropped_count)``.
    """
    kept: list[SalesRow] = []
    dropped = 0
    for row in rows:
        if row.business_date is None:
            kept.append(row)
            continue
        if start is not None and row.business_date < start:
            dropped += 1
            continue
        if end is not None and row.business_date > end:
            dropped += 1
            continue
        kept.append(row)
    return kept, dropped
