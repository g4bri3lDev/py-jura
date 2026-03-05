"""
Machine definitions registry for JURA coffee machines.

Maps article number (from BLE advertisement bytes 4-5) to MachineDefinition.

Machine modules (ef*.py) are discovered automatically - adding a new file
to this package is enough to register it. No changes to this file needed.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType

from py_jura.models import Alert
from py_jura.products import Product, ProductDefinition


@dataclass(frozen=True)
class MachineDefinition:
    """
    Full specification of a JURA machine model.

    `products` maps Product enum members to their ProductDefinition for this
    specific machine (option ranges and defaults vary per model).
    `alerts` maps alert bit numbers to Alert instances.
    `maintenance_counter_types` gives the ordered slot names for MAINTENANCE_COUNTER stats.
    `maintenance_percent_types` gives the ordered slot names for MAINTENANCE_PERCENT stats.
    """

    name: str
    products: dict[Product, ProductDefinition]
    alerts: dict[int, Alert]
    maintenance_counter_types: tuple[str, ...] = field(default_factory=tuple)
    maintenance_percent_types: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Global registries
# ---------------------------------------------------------------------------

MACHINES: dict[int, MachineDefinition] = {}
ARTICLE_NAMES: dict[int, str] = {}


def _register(definition: MachineDefinition, article_numbers: tuple[int, ...]) -> None:
    for article in article_numbers:
        MACHINES[article] = definition


def _load(mod: ModuleType) -> None:
    _register(
        MachineDefinition(
            name=mod.__name__.split(".")[-1].upper(),
            products=mod.PRODUCTS,
            alerts=mod.ALERTS,
            maintenance_counter_types=mod.MAINTENANCE_COUNTER_TYPES,
            maintenance_percent_types=mod.MAINTENANCE_PERCENT_TYPES,
        ),
        mod.ARTICLE_NUMBERS,
    )
    ARTICLE_NAMES.update(mod.ARTICLE_NAMES)


for _info in pkgutil.iter_modules(__path__):
    if _info.name.startswith("ef"):
        _load(importlib.import_module(f".{_info.name}", package=__name__))
