"""Header-row discovery shared by the XLSX and CSV parsers."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from ..normalize import normalize_header, resolve_columns

TOTALS_LABELS = frozenset({"total", "totals", "grand total", "sum", "subtotal"})


def find_header_row(
    rows: Sequence[Sequence[Any]],
    aliases: dict[str, Iterable[str]],
    required_any: Iterable[str] = ("menu_item", "qty"),
    max_scan: int = 15,
) -> tuple[int, dict[str, int], list[str], list[str]] | None:
    """Locate the header row in the first ``max_scan`` rows of a sheet or file.

    Toast exports sometimes carry a title/date banner above the real header, and
    the header itself varies between exports, so the header is found by scoring
    candidate rows against the alias table rather than assumed to be row 1.

    Args:
        rows: Raw rows, in file order.
        aliases: Alias table from :mod:`thbev.ingest.columns`.
        required_any: The candidate must bind at least one of these fields.
        max_scan: How many leading rows to consider.

    Returns:
        ``(row_index, index_by_field, missing_fields, unrecognized_headers)`` for
        the best candidate, or None when no row looks like a header.
    """
    best: tuple[int, int, dict[str, int], list[str], list[str]] | None = None
    for index, row in enumerate(rows[:max_scan]):
        if not any(normalize_header(cell) for cell in row):
            continue
        bound, missing, unrecognized = resolve_columns(row, aliases)
        if not any(field in bound for field in required_any):
            continue
        score = len(bound)
        if score < 2:
            continue
        if best is None or score > best[0]:
            best = (score, index, bound, missing, unrecognized)
    if best is None:
        return None
    _, index, bound, missing, unrecognized = best
    return index, bound, missing, unrecognized


def is_blank_row(row: Sequence[Any]) -> bool:
    """True when every cell is empty or whitespace."""
    return all(cell is None or str(cell).strip() == "" for cell in row)


def looks_like_totals_row(
    row: Sequence[Any], index_by_field: dict[str, int], label_fields: Iterable[str]
) -> bool:
    """Detect a trailing totals row.

    Two shapes occur: an explicit ``Total`` label in a text column, and the
    ItemSelectionDetails shape where every field is empty except ``Qty``.
    """
    from ..normalize import cell as read_cell

    for field in label_fields:
        value = read_cell(row, index_by_field, field)
        if value is not None and normalize_header(value) in TOTALS_LABELS:
            return True
    text_fields = [f for f in index_by_field if f not in ("qty", "net_price")]
    if not text_fields:
        return False
    all_text_blank = all(
        read_cell(row, index_by_field, f) is None or str(read_cell(row, index_by_field, f)).strip() == ""
        for f in text_fields
    )
    qty_present = read_cell(row, index_by_field, "qty") not in (None, "")
    return all_text_blank and qty_present
