"""POS sales -> product depletion."""

from .engine import DepletionEngine, DepletionLine, DepletionResult, packs_for_units

__all__ = ["DepletionEngine", "DepletionLine", "DepletionResult", "packs_for_units"]
