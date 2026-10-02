"""Placeholder for a future direct Toast integration.

**Nothing in this module talks to Toast.** There is no Toast connector in the
account, no credentials in this environment, and no verified endpoint contract.
Rather than guess at URLs or an auth flow -- which would produce code that looks
finished and fails in a way nobody can debug -- this source states exactly what
is unknown and refuses to run.

Its only job today is to prove the seam: when the integration is real, the
ordering engine changes by one line of config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from ..models import IngestResult
from ..timeutil import DEFAULT_CUTOFF_HOUR
from .base import SalesSource

#: What has to be established before a line of client code can be written.
#: Each entry is a genuine unknown, not a config field waiting to be filled in.
OPEN_QUESTIONS: tuple[dict[str, str], ...] = (
    {
        "id": "access_path",
        "question": "Which Toast access path are we granted?",
        "detail": (
            "Toast exposes integrations through its partner program; whether TownHall "
            "gets partner API access, a restaurant-level API credential, or neither is "
            "unresolved. The answer determines the auth model, the base host, and the "
            "lead time. None of it can be inferred."
        ),
    },
    {
        "id": "auth",
        "question": "What credential type and refresh model applies?",
        "detail": (
            "Client id/secret, bearer token lifetime, refresh mechanics and the header "
            "the token rides in are all unverified. No values are hardcoded here."
        ),
    },
    {
        "id": "host",
        "question": "What is the API host for this account's region?",
        "detail": "Unknown and deliberately not guessed. Supply via config once confirmed.",
    },
    {
        "id": "restaurant_id",
        "question": "What is the Short North location's Toast restaurant GUID?",
        "detail": (
            "Required to scope every request. The account is multi-location -- the "
            "recovered exports include FWD Day & Nightclub and TownHall Ohio City -- so "
            "an unscoped pull would mix concepts."
        ),
    },
    {
        "id": "report_availability",
        "question": "Are PMIX and ItemSelectionDetails reachable through the API at all?",
        "detail": (
            "The API surface may expose raw orders rather than the analytics reports the "
            "manual export produces. If it returns orders, this source has to reconstruct "
            "menu/menu group/sales category per selection itself, which is a different "
            "and larger piece of work than reformatting a report."
        ),
    },
    {
        "id": "business_day",
        "question": "Does the API apply the 4:00 AM business-day close, or return wall-clock UTC?",
        "detail": (
            "If timestamps come back in UTC, they must be converted to America/New_York "
            "before business_day_of() is applied, or every late-night sale lands on the "
            "wrong business day."
        ),
    },
    {
        "id": "voids_comps",
        "question": "How are voids and comps represented?",
        "detail": (
            "The CSV carries an explicit Void? flag. The API representation is unknown; "
            "voids must stay excluded and comps must stay counted-and-flagged."
        ),
    },
    {
        "id": "modifiers",
        "question": "Are modifier selections returned per line item?",
        "detail": (
            "This is the one thing the API could fix that the manual export currently "
            "cannot: no modifier-level export exists in the account today, so every "
            "spirit pour defaults to a 1.5 oz Single and every rocks and double pour "
            "is undercounted."
        ),
    },
    {
        "id": "rate_limits",
        "question": "What are the rate limits and pagination semantics?",
        "detail": "Unknown. Affects whether a week can be pulled in one call.",
    },
)


@dataclass
class ToastApiConfig:
    """Configuration a real Toast source would need. Every field is unverified.

    Present so the shape of the eventual config is visible and testable, not
    because these values are known to be correct.
    """

    host: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    restaurant_guid: str | None = None
    timezone: str = "America/New_York"
    cutoff_hour: int = DEFAULT_CUTOFF_HOUR
    extra: dict[str, Any] = field(default_factory=dict)

    def missing_fields(self) -> list[str]:
        """Names of required fields that are still unset."""
        required = ("host", "client_id", "client_secret", "restaurant_guid")
        return [name for name in required if not getattr(self, name)]


class ToastApiSource(SalesSource):
    """Documented stub. Constructing it is fine; calling it is not.

    Args:
        config: A :class:`ToastApiConfig`, or None.

    Raises:
        NotImplementedError: From :meth:`fetch_sales`, always.
    """

    name = "toast_api"

    def __init__(self, config: ToastApiConfig | None = None) -> None:
        self.config = config or ToastApiConfig()

    def fetch_sales(self, start: date, end: date) -> IngestResult:
        """Always raises. See :data:`OPEN_QUESTIONS`.

        Raises:
            NotImplementedError: With the full list of what must be resolved
                before this can be implemented.
        """
        raise NotImplementedError(self.blocking_message(start, end))

    def blocking_message(self, start: date | None = None, end: date | None = None) -> str:
        """Return the explanation of why this source cannot run."""
        window = f" for {start}..{end}" if start and end else ""
        lines = [
            f"ToastApiSource cannot fetch sales{window}: there is no Toast API integration yet.",
            "",
            "No endpoint, auth flow, or credential is implemented here on purpose -- "
            "guessing at them would produce a client that looks complete and silently "
            "returns nothing. Use FileUploadSource with a manual Toast export until the "
            "following are resolved:",
            "",
        ]
        for index, item in enumerate(OPEN_QUESTIONS, start=1):
            lines.append(f"  {index}. {item['question']}")
            lines.append(f"     {item['detail']}")
        missing = self.config.missing_fields()
        if missing:
            lines += ["", f"Config fields still unset: {', '.join(missing)}."]
        lines += [
            "",
            "Interim path that needs no API: configure a scheduled export inside Toast "
            "that emails ItemSelectionDetails to a dedicated inbox, and confirm Toast "
            "attaches it as a file rather than rendering it in the message body. That "
            "reuses this package's parsers unchanged.",
        ]
        return "\n".join(lines)

    def describe(self) -> dict[str, Any]:
        """Report the stub's state and everything blocking it."""
        return {
            "name": self.name,
            "type": type(self).__name__,
            "implemented": False,
            "config_missing": self.config.missing_fields(),
            "open_questions": [dict(q) for q in OPEN_QUESTIONS],
        }
