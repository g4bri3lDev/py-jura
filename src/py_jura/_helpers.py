"""Shared factory helpers for machine product-option definitions."""

from __future__ import annotations

from py_jura.products import RangeOption


def _water(min_ml: int, max_ml: int, default: int) -> RangeOption:
    """Water-amount option: arg=4, step=5 ml."""
    return RangeOption(arg=4, min=min_ml, max=max_ml, step=5, default=default)


def _milk(default: int) -> RangeOption:
    """Milk-amount option: arg=5, range 3–120 ml, step=1."""
    return RangeOption(arg=5, min=3, max=120, step=1, default=default)


def _milk_break(default: int) -> RangeOption:
    """Milk-break option: arg=11, range 0–60, step=1."""
    return RangeOption(arg=11, min=0, max=60, step=1, default=default)
