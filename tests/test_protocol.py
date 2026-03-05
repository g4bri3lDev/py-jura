"""Tests for BLE protocol command builders and status parsing."""

import pytest

from py_jura.encoder import encdec
from py_jura.products import (
    Product,
    ProductDefinition,
    RangeOption,
    StrengthOption,
    Temperature,
    TemperatureOption,
)
from py_jura.protocol import (
    build_brew_command,
    build_cancel_brew_command,
    build_disconnect_command,
    build_heartbeat_command,
    build_lock_command,
    build_shutdown_command,
    build_unlock_command,
    parse_alert_bits,
)

KEY = 0x2A


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def espresso_def() -> ProductDefinition:
    """EF533 Espresso definition (from XML)."""
    return ProductDefinition(
        product=Product.ESPRESSO,
        name="Espresso",
        strength=StrengthOption(arg=3, values=tuple(range(1, 9)), default=4),
        water=RangeOption(arg=4, min=15, max=80, step=5, default=45),
        temperature=TemperatureOption(
            arg=7,
            options=(Temperature.NORMAL, Temperature.HIGH),
            default=Temperature.HIGH,
        ),
    )


@pytest.fixture
def cappuccino_def() -> ProductDefinition:
    """EF533 Cappuccino definition (from XML)."""
    return ProductDefinition(
        product=Product.CAPPUCCINO,
        name="Cappuccino",
        strength=StrengthOption(arg=3, values=tuple(range(1, 9)), default=4),
        water=RangeOption(arg=4, min=25, max=240, step=5, default=60),
        temperature=TemperatureOption(
            arg=7,
            options=(Temperature.NORMAL, Temperature.HIGH),
            default=Temperature.NORMAL,
        ),
        milk=RangeOption(arg=5, min=3, max=120, step=1, default=14),
    )


@pytest.fixture
def milk_portion_def() -> ProductDefinition:
    """EF533 Milk Portion definition - no strength, water, or temperature."""
    return ProductDefinition(
        product=Product.MILK_PORTION,
        name="Milk Portion",
        milk=RangeOption(arg=5, min=3, max=120, step=1, default=30),
    )


# ---------------------------------------------------------------------------
# Brew command - structure
# ---------------------------------------------------------------------------


class TestBrewCommand:
    def test_length(self, espresso_def):
        assert len(build_brew_command(espresso_def, KEY)) == 18

    def test_byte0_is_key_after_decode(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY), KEY)
        assert decoded[0] == KEY

    def test_byte17_is_key_after_decode(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY), KEY)
        assert decoded[17] == KEY

    def test_product_code_at_byte1(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY), KEY)
        assert decoded[1] == Product.ESPRESSO.value

    def test_espresso_defaults(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY), KEY)
        assert decoded[3] == 4  # strength default (F3)
        assert decoded[4] == 9  # 45ml // 5 (F4)
        assert decoded[7] == 0x02  # Temperature.HIGH (F7)

    def test_espresso_custom_strength(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY, strength=8), KEY)
        assert decoded[3] == 8

    def test_espresso_custom_water(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY, water_ml=60), KEY)
        assert decoded[4] == 12  # 60ml // 5

    def test_espresso_custom_temperature(self, espresso_def):
        decoded = encdec(build_brew_command(espresso_def, KEY, temperature=Temperature.NORMAL), KEY)
        assert decoded[7] == Temperature.NORMAL.value

    def test_cappuccino_milk_at_byte5(self, cappuccino_def):
        decoded = encdec(build_brew_command(cappuccino_def, KEY), KEY)
        assert decoded[5] == 14  # 14ml // 1 (F5)

    def test_cappuccino_custom_milk(self, cappuccino_def):
        decoded = encdec(build_brew_command(cappuccino_def, KEY, milk_ml=30), KEY)
        assert decoded[5] == 30

    def test_milk_only_product(self, milk_portion_def):
        decoded = encdec(build_brew_command(milk_portion_def, KEY), KEY)
        assert decoded[1] == Product.MILK_PORTION.value
        assert decoded[3] == 0  # no strength
        assert decoded[7] == 0  # no temperature
        assert decoded[5] == 30  # default milk 30ml // 1


# ---------------------------------------------------------------------------
# P_MODE commands
# ---------------------------------------------------------------------------


class TestPModeCommands:
    def _decode(self, cmd: bytes) -> bytes:
        return encdec(cmd, KEY)

    def test_heartbeat_byte0_is_key(self):
        assert self._decode(build_heartbeat_command(KEY))[0] == KEY

    def test_heartbeat_payload(self):
        decoded = self._decode(build_heartbeat_command(KEY))
        assert decoded[1] == 0x7F
        assert decoded[2] == 0x80

    def test_heartbeat_no_override_key(self):
        decoded = self._decode(build_heartbeat_command(KEY))
        assert decoded[-1] != KEY  # last byte is NOT key

    def test_disconnect_payload(self):
        decoded = self._decode(build_disconnect_command(KEY))
        assert decoded[1] == 0x7F
        assert decoded[2] == 0x81

    def test_shutdown_payload(self):
        decoded = self._decode(build_shutdown_command(KEY))
        assert decoded[1] == 0x46
        assert decoded[2] == 0x02


# ---------------------------------------------------------------------------
# Barista (lock/unlock) commands
# ---------------------------------------------------------------------------


class TestBaristaCommands:
    def test_lock_payload(self):
        decoded = encdec(build_lock_command(KEY), KEY)
        assert decoded[0] == KEY
        assert decoded[1] == 0x01

    def test_unlock_payload(self):
        decoded = encdec(build_unlock_command(KEY), KEY)
        assert decoded[0] == KEY
        assert decoded[1] == 0x00


# ---------------------------------------------------------------------------
# Alert bit parsing
# ---------------------------------------------------------------------------


class TestParseAlertBits:
    def test_no_alerts(self):
        # All zeros after decode = no alerts
        data = encdec(bytes(20), KEY)
        assert parse_alert_bits(data, KEY) == []

    def test_bit0_active(self):
        raw = bytearray(20)
        raw[1] = 0b10000000  # bit 0 (MSB of byte 1)
        data = encdec(bytes(raw), KEY)
        assert 0 in parse_alert_bits(data, KEY)

    def test_bit1_active(self):
        raw = bytearray(20)
        raw[1] = 0b01000000  # bit 1
        data = encdec(bytes(raw), KEY)
        assert 1 in parse_alert_bits(data, KEY)

    def test_multiple_bits(self):
        raw = bytearray(20)
        raw[1] = 0b10000010  # bits 0 and 6
        data = encdec(bytes(raw), KEY)
        active = parse_alert_bits(data, KEY)
        assert 0 in active
        assert 6 in active


# ---------------------------------------------------------------------------
# build_cancel_brew_command
# ---------------------------------------------------------------------------


class TestBuildCancelBrewCommand:
    def test_length_is_2(self):
        assert len(build_cancel_brew_command(KEY)) == 2

    def test_decoded_second_byte_is_0xff(self):
        cmd = build_cancel_brew_command(KEY)
        decoded = encdec(bytes(cmd), KEY)
        assert decoded[1] == 0xFF

    def test_decoded_first_byte_is_key(self):
        cmd = build_cancel_brew_command(KEY)
        decoded = encdec(bytes(cmd), KEY)
        assert decoded[0] == KEY
