"""The working sales source: files a manager exported from Toast by hand.

This is the only path that functions today. Toast has no connector in the
account, no scheduled export exists, and the daily email Toast does send is an
HTML body with no attachment -- so manual upload is it.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Iterable

from ..ingest import detect_format, parse_item_selection_details, parse_pmix
from ..models import IngestResult, Severity, filter_rows_to_range
from ..timeutil import DEFAULT_CUTOFF_HOUR
from .base import SalesSource


class FileUploadSource(SalesSource):
    """Read Toast exports from local files.

    Accepts any mix of PMIX workbooks and ItemSelectionDetails CSVs. Format is
    detected per file from the extension and header row, so the caller does not
    have to say which is which.

    Args:
        paths: Files to read.
        location: Toast location name to filter to, for exports that carry a
            ``Location`` column.
        cutoff_hour: Business-day rollover hour. 4 AM at TownHall.
        include_comps: Comps count as depletion and stay flagged.
        prefer_pmix_sheet: ``"all_levels"`` or ``"items"``.
    """

    name = "file_upload"

    def __init__(
        self,
        paths: Iterable[str | Path],
        *,
        location: str | None = None,
        cutoff_hour: int = DEFAULT_CUTOFF_HOUR,
        include_comps: bool = True,
        prefer_pmix_sheet: str = "all_levels",
    ) -> None:
        self.paths: list[Path] = [Path(p) for p in paths]
        if not self.paths:
            raise ValueError("FileUploadSource needs at least one export file.")
        self.location = location
        self.cutoff_hour = cutoff_hour
        self.include_comps = include_comps
        self.prefer_pmix_sheet = prefer_pmix_sheet

    def fetch_sales(self, start: date, end: date) -> IngestResult:
        """Parse every configured file and return one merged result.

        PMIX rows carry no date, so they are kept regardless of the range -- the
        export's own range is the filter for those -- and a warning records that
        the range could not be enforced.
        """
        merged = IngestResult()
        for path in self.paths:
            kind = detect_format(path)
            if kind == "pmix":
                result = parse_pmix(path, prefer=self.prefer_pmix_sheet)
                if result.rows:
                    merged.add_issue(
                        Severity.INFO,
                        "pmix_range_not_enforced",
                        f"{path.name} is a PMIX aggregate with no time dimension; the "
                        f"requested range {start}..{end} could not be enforced on it, and "
                        "it cannot support the post-cutoff adjustment.",
                        file=str(path),
                    )
            elif kind == "item_selection_details":
                result = parse_item_selection_details(
                    path,
                    location=self.location,
                    cutoff_hour=self.cutoff_hour,
                    start=start,
                    end=end,
                    include_comps=self.include_comps,
                )
            else:
                merged.add_issue(
                    Severity.ERROR,
                    "unrecognized_file",
                    f"{path.name} is not a recognizable Toast PMIX workbook or "
                    "ItemSelectionDetails CSV; it was not read.",
                    file=str(path),
                )
                continue
            merged.extend(result)

        kept, dropped = filter_rows_to_range(merged.rows, start, end)
        if dropped:
            merged.bump("rows_outside_range", dropped)
        merged.rows = kept
        return merged

    def describe(self) -> dict[str, Any]:
        """Configuration echo, including the detected format of each file."""
        return {
            "name": self.name,
            "type": type(self).__name__,
            "location": self.location,
            "cutoff_hour": self.cutoff_hour,
            "files": [{"path": str(p), "format": detect_format(p)} for p in self.paths],
        }
