"""Header, name and value normalization.

Toast exports vary column *sets* and column *order* between exports from the
same account, so every column lookup in this package resolves by normalized
header name. Nothing in :mod:`thbev.ingest` may index a row by position.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Sequence

_PUNCT = re.compile(r"[^a-z0-9]+")
_WS = re.compile(r"\s+")

TRUEISH = {"true", "t", "yes", "y", "1"}
FALSEISH = {"false", "f", "no", "n", "0", ""}


def normalize_header(value: Any) -> str:
    """Normalize a header cell to a comparison key.

    Lowercases, strips, replaces every run of punctuation/whitespace with a
    single space. ``"Item, open item"`` -> ``"item open item"``;
    ``"Void?"`` -> ``"void"``; ``"Avg. price"`` -> ``"avg price"``.
    """
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def normalize_key(value: Any) -> str:
    """Normalize a data value used as part of a mapping key.

    Case- and punctuation-insensitive but whitespace preserving as single
    spaces, so ``"Espolon BLANCO"`` and ``"espolon blanco"`` collide while
    ``"Bud Light"`` and ``"Bud Lt"`` do not.
    """
    return normalize_header(value)


def squash(value: Any) -> str:
    """Normalize by removing *all* separators.

    Used for enum-ish values whose spelling varies: ``"menuItem"``,
    ``"Menu Item"`` and ``"menu_item"`` all become ``"menuitem"``.
    """
    if value is None:
        return ""
    return _PUNCT.sub("", str(value).strip().lower())


def clean_text(value: Any) -> str | None:
    """Trim a cell to a string, returning None for blanks."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_bool(value: Any) -> bool | None:
    """Parse Toast's ``TRUE``/``FALSE`` text flags. Returns None if unreadable."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in TRUEISH:
        return True
    if text in FALSEISH:
        return False
    return None


def parse_number(value: Any) -> float | None:
    """Parse a quantity or price cell. Returns None if it is not a number.

    Handles ``"1,234"``, ``"$8.75"``, ``"(3)"`` (accounting negative) and
    already-numeric cells from openpyxl.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = text.replace(",", "").replace("$", "").strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def resolve_columns(
    header_row: Sequence[Any], aliases: dict[str, Iterable[str]]
) -> tuple[dict[str, int], list[str], list[str]]:
    """Map logical field names to column indexes by normalized header.

    Args:
        header_row: The raw header cells, in file order.
        aliases: ``{logical_field: [accepted normalized header, ...]}``. The
            first alias that appears in the header row wins; earlier aliases
            take precedence so a file carrying both ``"Menu Item"`` and
            ``"Item"`` binds the more specific one.

    Returns:
        ``(index_by_field, missing_fields, unrecognized_headers)``. Every field
        is optional by contract -- callers decide what they can live without --
        so absence is reported, never raised.
    """
    normalized = [normalize_header(cell) for cell in header_row]
    seen_positions: set[int] = set()
    index_by_field: dict[str, int] = {}
    for field, options in aliases.items():
        for option in options:
            if option in normalized:
                position = normalized.index(option)
                if position in seen_positions:
                    continue
                index_by_field[field] = position
                seen_positions.add(position)
                break
    missing = [field for field in aliases if field not in index_by_field]
    unrecognized = [
        normalized[i] for i in range(len(normalized)) if normalized[i] and i not in seen_positions
    ]
    return index_by_field, missing, unrecognized


def cell(row: Sequence[Any], index_by_field: dict[str, int], field: str) -> Any:
    """Read a field from a row by logical name, tolerating short rows."""
    position = index_by_field.get(field)
    if position is None or position >= len(row):
        return None
    return row[position]
