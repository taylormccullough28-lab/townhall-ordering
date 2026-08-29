"""Parser for Toast ItemSelectionDetails CSV exports.

Observed header, verbatim::

    Location,Order #,Sent Date,Menu Item,Menu Group,Menu,Sales Category,Net Price,Qty,Void?

This is the richer of the two inputs: one row per sale, with a timestamp. The
timestamp is what the post-cutoff depletion adjustment runs on -- PMIX is
aggregated and cannot answer "how much sells between a 5 PM Sunday cutoff and
4 AM close".

Three file-specific hazards, all handled here:

* ``Location`` matters in a multi-location Toast account; rows are filtered to
  the configured location and the non-matching count is reported.
* ``Void?`` is explicit ``TRUE``/``FALSE``. Voids are excluded from ``rows`` and
  kept in ``voided`` so the exclusion is auditable.
* The file ends with a totals row -- every field blank except ``Qty``. Counting
  it inflates the week.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..models import IngestResult, ItemKey, SalesRow, Severity, UnmappedRow
from ..normalize import cell, clean_text, normalize_key, parse_bool, parse_number
from ..timeutil import DEFAULT_CUTOFF_HOUR, business_day_of
from .columns import ITEM_SELECTION_ALIASES
from .sheets import find_header_row, is_blank_row, looks_like_totals_row

#: Timestamp spellings seen in, or plausible for, Toast exports.
DATE_FORMATS: tuple[str, ...] = (
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%y %H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%m/%d/%Y",
    "%Y-%m-%d",
)


def parse_sent_date(value: Any) -> datetime | None:
    """Parse a Toast ``Sent Date`` cell into a naive local datetime.

    Returns None when the value is blank or in an unrecognized format; the
    caller records that as an issue rather than dropping the row.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_item_selection_details(
    path: str | Path,
    *,
    location: str | None = None,
    cutoff_hour: int = DEFAULT_CUTOFF_HOUR,
    start: date | None = None,
    end: date | None = None,
    include_comps: bool = True,
) -> IngestResult:
    """Parse an ItemSelectionDetails CSV into normalized sales rows.

    Args:
        path: Path to the ``.csv`` export.
        location: Toast location name to keep, e.g. ``"Townhall - Short North"``.
            Matched case- and punctuation-insensitively. None keeps every row and
            raises a warning issue if more than one location is present.
        cutoff_hour: Business-day rollover hour; 4 AM for TownHall.
        start: Optional inclusive business-date lower bound.
        end: Optional inclusive business-date upper bound.
        include_comps: Comps count as depletion (and stay flagged). Set False to
            exclude them, which is not the PRD behaviour.

    Returns:
        An :class:`~thbev.models.IngestResult` whose rows carry ``sold_at`` and
        ``business_date``, so downstream code can prorate by hour.

    Raises:
        FileNotFoundError: If the CSV does not exist.
        ValueError: If no header row can be identified.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"ItemSelectionDetails CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        raw_rows = [tuple(row) for row in csv.reader(handle)]

    result = IngestResult(source_files=[str(path)])
    header = find_header_row(raw_rows, ITEM_SELECTION_ALIASES)
    if header is None:
        raise ValueError(
            f"{path}: no recognizable ItemSelectionDetails header row found in the "
            "first rows of the file. Expected columns such as 'Menu Item' and 'Qty'."
        )
    header_index, columns, missing, unrecognized = header
    result.missing_columns[path.name] = missing
    _report_missing(result, missing, path.name)
    if unrecognized:
        result.add_issue(
            Severity.INFO,
            "unrecognized_columns",
            f"Columns this parser does not use: {', '.join(unrecognized)}.",
            columns=unrecognized,
        )

    wanted_location = normalize_key(location) if location else None
    locations_seen: set[str] = set()

    for offset, row in enumerate(raw_rows[header_index + 1 :], start=header_index + 2):
        if is_blank_row(row):
            continue
        raw = {field: cell(row, columns, field) for field in columns}

        if looks_like_totals_row(row, columns, ("menu_item", "location")):
            result.bump("totals_rows_dropped")
            result.add_issue(
                Severity.INFO,
                "totals_row_dropped",
                f"Dropped a trailing totals row at line {offset}.",
                line=offset,
            )
            continue

        row_location = clean_text(cell(row, columns, "location"))
        if row_location:
            locations_seen.add(row_location)
        if wanted_location is not None and normalize_key(row_location) != wanted_location:
            result.bump("rows_filtered_other_location")
            continue

        qty = parse_number(cell(row, columns, "qty"))
        item = clean_text(cell(row, columns, "menu_item"))
        key = ItemKey(
            sales_category=clean_text(cell(row, columns, "sales_category")),
            menu=clean_text(cell(row, columns, "menu")),
            menu_group=clean_text(cell(row, columns, "menu_group")),
            menu_item=item,
        )

        if item is None or qty is None:
            result.unmapped.append(
                UnmappedRow(
                    reason="blank menu item" if item is None else "unreadable quantity",
                    qty=qty,
                    source=f"item_selection_details:{path.name}",
                    row_number=offset,
                    key=key,
                    raw=raw,
                )
            )
            continue

        void_raw = cell(row, columns, "void")
        voided = parse_bool(void_raw)
        if voided is None and void_raw not in (None, ""):
            result.add_issue(
                Severity.WARNING,
                "unreadable_void_flag",
                f"Line {offset}: Void? value {void_raw!r} is not TRUE/FALSE; treated as not voided.",
                line=offset,
            )
            voided = False
        voided = bool(voided)

        comped = bool(parse_bool(cell(row, columns, "comp"))) if "comp" in columns else False

        sold_at = parse_sent_date(cell(row, columns, "sent_date"))
        if sold_at is None and "sent_date" in columns:
            result.bump("rows_without_timestamp")
        business_date = business_day_of(sold_at, cutoff_hour) if sold_at else None

        modifiers = _split_modifiers(cell(row, columns, "modifiers"))

        sales_row = SalesRow(
            key=key,
            qty=qty,
            source=f"item_selection_details:{path.name}",
            sold_at=sold_at,
            business_date=business_date,
            location=row_location,
            order_id=clean_text(cell(row, columns, "order_id")),
            net_price=parse_number(cell(row, columns, "net_price")),
            voided=voided,
            comped=comped,
            modifiers=modifiers,
            row_number=offset,
            raw=raw,
        )

        if voided:
            result.voided.append(sales_row)
            result.bump("voids_excluded")
            continue

        if comped:
            result.bump("comps_included")
            if not include_comps:
                result.bump("comps_excluded_by_config")
                continue

        if business_date is not None:
            if start is not None and business_date < start:
                result.bump("rows_outside_range")
                continue
            if end is not None and business_date > end:
                result.bump("rows_outside_range")
                continue

        result.rows.append(sales_row)

    if wanted_location is None and len(locations_seen) > 1:
        result.add_issue(
            Severity.WARNING,
            "multiple_locations",
            "No location filter was given and this file contains more than one "
            f"location ({', '.join(sorted(locations_seen))}). Quantities are mixed across locations.",
            locations=sorted(locations_seen),
        )
    if wanted_location is not None and not result.rows:
        result.add_issue(
            Severity.ERROR,
            "location_matched_nothing",
            f"Location filter {location!r} matched no rows. Locations present: "
            f"{', '.join(sorted(locations_seen)) or '(none)'}.",
            locations=sorted(locations_seen),
        )
    result.sheets_present.append(path.name)
    result.sheets_used.append(path.name)
    return result


def _split_modifiers(value: Any) -> tuple[str, ...]:
    text = clean_text(value)
    if not text:
        return ()
    parts = [p.strip() for p in text.replace(";", ",").split(",")]
    return tuple(p for p in parts if p)


def _report_missing(result: IngestResult, missing: Iterable[str], name: str) -> None:
    missing = list(missing)
    if "void" in missing:
        result.add_issue(
            Severity.WARNING,
            "no_void_column",
            f"{name}: no Void? column. Voided sales cannot be excluded and will be counted as depletion.",
        )
    if "sent_date" in missing:
        result.add_issue(
            Severity.WARNING,
            "no_timestamp_column",
            f"{name}: no Sent Date column. Business-day bucketing and the post-cutoff "
            "adjustment are both unavailable for this file.",
        )
    if "location" in missing:
        result.add_issue(
            Severity.WARNING,
            "no_location_column",
            f"{name}: no Location column; rows cannot be filtered to a single location.",
        )
    if "sales_category" in missing:
        result.add_issue(
            Severity.INFO,
            "no_sales_category_column",
            f"{name}: no Sales Category column. Classification falls back entirely to "
            "the product mapping on menu + menu group + item.",
        )


def detect_format(path: str | Path) -> str:
    """Return ``"item_selection_details"``, ``"pmix"`` or ``"unknown"`` for a file.

    Extension decides first (``.xlsx``/``.xlsm`` are always PMIX workbooks); for
    CSVs the header row is sniffed so a future flat PMIX CSV is not mistaken for
    a line-item export.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        return "pmix"
    if suffix not in (".csv", ".tsv", ".txt"):
        return "unknown"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        head = [tuple(row) for _, row in zip(range(15), csv.reader(handle))]
    if find_header_row(head, ITEM_SELECTION_ALIASES, required_any=("sent_date", "void")):
        return "item_selection_details"
    from .columns import ALL_LEVELS_ALIASES

    if find_header_row(head, ALL_LEVELS_ALIASES, required_any=("type", "qty")):
        return "pmix"
    return "unknown"
