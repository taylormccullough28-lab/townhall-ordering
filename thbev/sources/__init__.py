"""Pluggable sales sources.

``FileUploadSource`` works today. ``ToastApiSource`` is a documented stub. Both
satisfy :class:`SalesSource`, so which one runs is a config choice.
"""

from __future__ import annotations

from typing import Any

from .base import SalesSource, SourceNotAvailable
from .file_upload import FileUploadSource
from .toast_api import OPEN_QUESTIONS, ToastApiConfig, ToastApiSource

#: Registry keyed by the value used in config files.
SOURCE_TYPES: dict[str, type[SalesSource]] = {
    "file_upload": FileUploadSource,
    "toast_api": ToastApiSource,
}


def build_source(config: dict[str, Any]) -> SalesSource:
    """Build a sales source from a config mapping.

    Args:
        config: ``{"type": "file_upload", ...}``. Remaining keys are passed to
            the source's constructor; ``toast_api`` takes a ``config`` mapping
            that becomes a :class:`ToastApiConfig`.

    Returns:
        A configured :class:`SalesSource`.

    Raises:
        ValueError: If ``type`` is missing or unknown.
    """
    options = dict(config)
    kind = options.pop("type", None)
    if kind is None:
        raise ValueError("Sales source config needs a 'type' key.")
    if kind not in SOURCE_TYPES:
        raise ValueError(
            f"Unknown sales source type {kind!r}. Known types: {', '.join(sorted(SOURCE_TYPES))}."
        )
    if kind == "toast_api":
        return ToastApiSource(ToastApiConfig(**options.get("config", {})))
    return SOURCE_TYPES[kind](**options)


__all__ = [
    "OPEN_QUESTIONS",
    "FileUploadSource",
    "SOURCE_TYPES",
    "SalesSource",
    "SourceNotAvailable",
    "ToastApiConfig",
    "ToastApiSource",
    "build_source",
]
