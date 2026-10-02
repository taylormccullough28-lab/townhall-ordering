"""The sales source seam.

Everything downstream of ingest consumes :class:`~thbev.models.IngestResult`.
Which system produced it -- a file a manager uploaded, or some future Toast API
-- is deliberately invisible past this interface, so switching inputs is a
config change rather than a rewrite.
"""

from __future__ import annotations

import abc
from datetime import date
from typing import Any

from ..models import IngestResult


class SalesSource(abc.ABC):
    """A source of normalized beverage sales for a business-date range."""

    #: Stable identifier used in config and in ingest provenance.
    name: str = "sales-source"

    @abc.abstractmethod
    def fetch_sales(self, start: date, end: date) -> IngestResult:
        """Return normalized sales rows for the inclusive business-date range.

        Args:
            start: First business date to include.
            end: Last business date to include.

        Returns:
            An :class:`~thbev.models.IngestResult`. Implementations must report
            what they could not read rather than returning fewer rows silently.
        """

    def describe(self) -> dict[str, Any]:
        """Human- and machine-readable description of this source's configuration."""
        return {"name": self.name, "type": type(self).__name__}


class SourceNotAvailable(RuntimeError):
    """Raised when a configured source cannot run in this environment."""
