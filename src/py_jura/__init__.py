"""py-jura - Python library for controlling JURA coffee machines over Bluetooth."""

from py_jura.exceptions import (
    JuraError,
    MachineBlockedError,
    MachineDisconnectedError,
    MachineNotFoundError,
    UnsupportedProductError,
)
from py_jura.machine import JuraMachine
from py_jura.machines import ARTICLE_NAMES
from py_jura.models import Alert, BrewProgress, MachineInfo, MachineStats, MachineStatus, MaintenanceStats
from py_jura.products import Product, Temperature

__version__ = "0.2.0"

__all__ = [
    "JuraMachine",
    "ARTICLE_NAMES",
    "Product",
    "Temperature",
    "MachineStatus",
    "MachineStats",
    "MachineInfo",
    "MaintenanceStats",
    "BrewProgress",
    "Alert",
    "JuraError",
    "MachineBlockedError",
    "MachineDisconnectedError",
    "MachineNotFoundError",
    "UnsupportedProductError",
]
