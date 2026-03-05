"""
Product definitions for JURA coffee machines.

Product codes are globally consistent across all JURA machines - the same
code always refers to the same drink type. Option specs (strength range,
water range, etc.) vary per machine and live in machines/*.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Product(Enum):
    """All known JURA product codes across all machines."""

    RISTRETTO = 0x01
    ESPRESSO = 0x02
    COFFEE = 0x03
    CAPPUCCINO = 0x04
    MILK_COFFEE = 0x05
    ESPRESSO_MACCHIATO = 0x06
    LATTE_MACCHIATO = 0x07
    MILK_FOAM = 0x08
    MILK_PORTION = 0x0A
    POT = 0x0C
    HOT_WATER = 0x0D
    TWO_RISTRETTI = 0x11
    TWO_ESPRESSI = 0x12
    TWO_COFFEES = 0x13
    TWO_CAPPUCCINI = 0x14
    TWO_MILK_COFFEES = 0x15
    TWO_ESPRESSO_MACCHIATI = 0x16
    TWO_LATTE_MACCHIATI = 0x17
    TWO_MILK_FOAM = 0x18
    TWO_MILK_PORTIONS = 0x1A
    HOT_WATER_GREEN_TEA = 0x2D
    FLAT_WHITE = 0x2E
    LUNGO_BARISTA = 0x2F
    ESPRESSO_DOPPIO = 0x30
    TWO_FLAT_WHITES = 0x3E
    TWO_LUNGO_BARISTAS = 0x3F
    CAFE_BARISTA = 0x28
    AMERICANO = 0x29
    MOCACCINO = 0x2A
    CORTADO = 0x2B
    RAF_COFFEE = 0x2C
    LONG_BLACK = 0x1B
    CHOCOLATE_MILK_FOAM = 0x1C
    TWO_ESPRESSI_ENA = 0x31  # ENA series uses different code
    XL_LUNGO = 0x32
    COFFEE_BIG = 0x33
    CAPPUCCINO_BIG = 0x34
    MILK_COFFEE_BIG = 0x35
    TWO_COFFEES_ENA = 0x36  # ENA series uses different code
    LATTE_MACCHIATO_BIG = 0x37
    TWO_CAFE_BARISTAS = 0x38
    TWO_LUNGOS = 0x39
    MILK_BIG = 0x3A
    TWO_CORTADOS = 0x3B
    POT_SPEED = 0x3C
    HOT_WATER_BIG = 0x3D


class Temperature(Enum):
    """Temperature options for JURA machines. Values are BLE wire values."""

    LOW = 0x00
    NORMAL = 0x01
    HIGH = 0x02


# ---------------------------------------------------------------------------
# Option spec types - used inside ProductDefinition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrengthOption:
    """
    Discrete strength levels.

    `values` are the valid wire values (ints sent over BLE).
    The user passes one of these ints directly to brew().
    """

    arg: int  # byte position in command (F-number)
    values: tuple[int, ...]  # valid wire values e.g. (1, 2, 3, 4, 5, 6, 7, 8)
    default: int  # default wire value


@dataclass(frozen=True)
class RangeOption:
    """
    Continuous range option (water amount, milk amount, milk break).

    User passes a value in ml. Wire value = ml // step.
    """

    arg: int  # byte position in command (F-number)
    min: int  # minimum in ml
    max: int  # maximum in ml
    step: int  # step size in ml
    default: int  # default in ml


@dataclass(frozen=True)
class TemperatureOption:
    """
    Discrete temperature levels.

    User passes a Temperature enum member. Wire value = member.value.
    """

    arg: int  # byte position in command (F-number)
    options: tuple[Temperature, ...]  # valid temperature options
    default: Temperature  # default temperature


# ---------------------------------------------------------------------------
# ProductDefinition - one instance per product per machine (in machines/*.py)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductDefinition:
    """
    Full specification of a product on a specific machine.

    All option fields are None if that option is not available for this
    product (e.g. a milk-only product has no strength option).
    """

    product: Product
    name: str
    strength: StrengthOption | None = None
    water: RangeOption | None = None
    temperature: TemperatureOption | None = None
    milk: RangeOption | None = None
    milk_break: RangeOption | None = None
