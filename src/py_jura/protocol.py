"""
BLE protocol constants and command builders for JURA coffee machines.

All UUIDs are from the JURA Smart Control BLE service.
Reference: Jutta-Proto/protocol-bt-cpp - CoffeeMaker.cpp
"""

from __future__ import annotations

from enum import IntEnum

from py_jura.encoder import encdec
from py_jura.products import ProductDefinition, Temperature


class StatMode(IntEnum):
    """Statistics request modes for the STATISTICS_COMMAND characteristic."""

    PRODUCT_COUNTERS = 1
    MAINTENANCE_COUNTER = 4
    MAINTENANCE_PERCENT = 8
    DAILY_COUNTERS = 16


# ---------------------------------------------------------------------------
# BLE UUIDs
# ---------------------------------------------------------------------------

SERVICE_UUID = "5a401523-ab2e-2548-c435-08c300000710"

ABOUT_MACHINE_UUID = "5a401531-ab2e-2548-c435-08c300000710"
MACHINE_STATUS_UUID = "5a401524-ab2e-2548-c435-08c300000710"
BARISTA_MODE_UUID = "5a401530-ab2e-2548-c435-08c300000710"
PRODUCT_PROGRESS_UUID = "5a401527-ab2e-2548-c435-08c300000710"
P_MODE_UUID = "5a401529-ab2e-2548-c435-08c300000710"
P_MODE_READ_UUID = "5a401538-ab2e-2548-c435-08c300000710"
START_PRODUCT_UUID = "5a401525-ab2e-2548-c435-08c300000710"
STATISTICS_COMMAND_UUID = "5a401533-ab2e-2548-c435-08c300000710"
STATISTICS_DATA_UUID = "5a401534-ab2e-2548-c435-08c300000710"
UPDATE_PRODUCT_UUID = "5a401528-ab2e-2548-c435-08c300000710"

UART_SERVICE_UUID = "5a401623-ab2e-2548-c435-08c300000710"
UART_RX_UUID = "5a401624-ab2e-2548-c435-08c300000710"
UART_TX_UUID = "5a401625-ab2e-2548-c435-08c300000710"

# ---------------------------------------------------------------------------
# Raw P_MODE payloads (before key injection and encoding)
# ---------------------------------------------------------------------------

_HEARTBEAT_PAYLOAD = bytes([0x00, 0x7F, 0x80])
_DISCONNECT_PAYLOAD = bytes([0x00, 0x7F, 0x81])
_SHUTDOWN_PAYLOAD = bytes([0x00, 0x46, 0x02])

# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------


def _encode_command(data: bytearray, key: int, override_key: bool) -> bytes:
    """Set byte[0] to key, optionally byte[-1], then encode."""
    data[0] = key
    if override_key:
        data[-1] = key
    return encdec(bytes(data), key)


def build_brew_command(
    product_def: ProductDefinition,
    key: int,
    strength: int | None = None,
    water_ml: int | None = None,
    temperature: Temperature | None = None,
    milk_ml: int | None = None,
    milk_break_ml: int | None = None,
) -> bytes:
    """
    Build and encode an 18-byte brew command for START_PRODUCT characteristic.

    Unset options fall back to the product's defaults. The caller is
    responsible for validating option values before calling this function.

    Wire encoding:
      - Strength:    wire = value (direct)
      - Water/milk:  wire = ml // step
      - Temperature: wire = temperature.value
    """
    data = bytearray(18)

    # byte[0] will be set to key by _encode_command
    data[1] = product_def.product.value

    if product_def.strength is not None:
        val = strength if strength is not None else product_def.strength.default
        data[product_def.strength.arg] = val

    if product_def.water is not None:
        ml = water_ml if water_ml is not None else product_def.water.default
        data[product_def.water.arg] = ml // product_def.water.step

    if product_def.temperature is not None:
        temp = temperature if temperature is not None else product_def.temperature.default
        data[product_def.temperature.arg] = temp.value

    if product_def.milk is not None:
        ml = milk_ml if milk_ml is not None else product_def.milk.default
        data[product_def.milk.arg] = ml // product_def.milk.step

    if product_def.milk_break is not None:
        ml = milk_break_ml if milk_break_ml is not None else product_def.milk_break.default
        data[product_def.milk_break.arg] = ml // product_def.milk_break.step

    return _encode_command(data, key, override_key=True)


def build_heartbeat_command(key: int) -> bytes:
    """Build the stay-in-BLE heartbeat command for P_MODE characteristic."""
    return _encode_command(bytearray(_HEARTBEAT_PAYLOAD), key, override_key=False)


def build_disconnect_command(key: int) -> bytes:
    """Build the graceful disconnect command for P_MODE characteristic."""
    return _encode_command(bytearray(_DISCONNECT_PAYLOAD), key, override_key=False)


def build_shutdown_command(key: int) -> bytes:
    """Build the machine shutdown command for P_MODE characteristic."""
    return _encode_command(bytearray(_SHUTDOWN_PAYLOAD), key, override_key=False)


def build_cancel_brew_command(key: int) -> bytes:
    """Build the brew cancellation command for UPDATE_PRODUCT characteristic."""
    return _encode_command(bytearray([0x00, 0xFF]), key, override_key=False)


def build_lock_command(key: int) -> bytes:
    """Build the screen lock command for BARISTA_MODE characteristic."""
    return _encode_command(bytearray([0x00, 0x01]), key, override_key=False)


def build_unlock_command(key: int) -> bytes:
    """Build the screen unlock command for BARISTA_MODE characteristic."""
    return _encode_command(bytearray([0x00, 0x00]), key, override_key=False)


def build_stats_command(key: int, mode: StatMode) -> bytes:
    """
    Build a 5-byte statistics request command for STATISTICS_COMMAND characteristic.

    Wire format (before encoding):
      byte[0]    = key  (set by _encode_command)
      byte[1]    = high byte of mode (always 0 for known modes)
      byte[2]    = low byte of mode
      byte[3]    = 0xFF  (force all products; per C++ reference)
      byte[4]    = key   (set by override_key=True)
    """
    data = bytearray(5)
    data[1] = (int(mode) & 0xFF00) >> 8
    data[2] = int(mode) & 0x00FF
    data[3] = 0xFF
    return _encode_command(data, key, override_key=True)


# ---------------------------------------------------------------------------
# Status parsing
# ---------------------------------------------------------------------------


def parse_alert_bits(data: bytes, key: int) -> list[int]:
    """
    Decode a MACHINE_STATUS characteristic payload and return active alert bits.

    The data is first decoded with encdec, then each bit (except byte 0)
    is checked MSB-first. Returns a list of active bit indices.
    """
    decoded = encdec(data, key)
    active: list[int] = []
    for i in range((len(decoded) - 1) * 8):
        byte_offset = (i >> 3) + 1
        bit_offset = 7 - (i & 0b111)
        if byte_offset < len(decoded) and (decoded[byte_offset] >> bit_offset) & 1:
            active.append(i)
    return active
