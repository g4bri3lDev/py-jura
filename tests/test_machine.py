"""
Tests for JuraMachine - mocking the BLE layer entirely.

Hardware tests (requiring a physical machine) are in test_machine_hardware.py
and are marked with @pytest.mark.hardware.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from py_jura.encoder import encdec
from py_jura.exceptions import (
    MachineBlockedError,
    MachineDisconnectedError,
    MachineNotFoundError,
    UnsupportedProductError,
)
from py_jura.machine import JuraMachine, _get_stat_val
from py_jura.machines import MACHINES
from py_jura.models import MachineStats, MachineStatus
from py_jura.products import Product, Temperature

# Key and article number from a known EF533 machine (15084 = E8)
_KEY = 0x2A
_ARTICLE = 15084


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_machine(key: int = _KEY, article: int = _ARTICLE) -> JuraMachine:
    """Create a JuraMachine with a mocked-in client and machine definition."""
    m = JuraMachine("AA:BB:CC:DD:EE:FF")
    m._key = key
    m._machine_def = MACHINES[article]

    mock_client = MagicMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    mock_client.read_gatt_char = AsyncMock()
    m._client = mock_client
    return m


# ---------------------------------------------------------------------------
# _parse_advertisement
# ---------------------------------------------------------------------------


class TestParseAdvertisement:
    def test_extracts_key_and_article(self):
        from bleak.backends.scanner import AdvertisementData

        raw = bytes([_KEY, 0x00, 0x00, 0x00, _ARTICLE & 0xFF, (_ARTICLE >> 8) & 0xFF])
        adv = AdvertisementData(
            local_name=None,
            manufacturer_data={0x00AB: raw},
            service_data={},
            service_uuids=[],
            platform_data=(),
            rssi=-60,
            tx_power=None,
        )
        key, article = JuraMachine._parse_advertisement(adv)
        assert key == _KEY
        assert article == _ARTICLE

    def test_raises_if_no_manufacturer_data(self):
        from bleak.backends.scanner import AdvertisementData

        adv = AdvertisementData(
            local_name=None,
            manufacturer_data={},
            service_data={},
            service_uuids=[],
            platform_data=(),
            rssi=-60,
            tx_power=None,
        )
        with pytest.raises(MachineNotFoundError):
            JuraMachine._parse_advertisement(adv)

    def test_raises_if_data_too_short(self):
        from bleak.backends.scanner import AdvertisementData

        adv = AdvertisementData(
            local_name=None,
            manufacturer_data={0x00AB: bytes([0x01, 0x02])},
            service_data={},
            service_uuids=[],
            platform_data=(),
            rssi=-60,
            tx_power=None,
        )
        with pytest.raises(MachineNotFoundError):
            JuraMachine._parse_advertisement(adv)

    def test_article_number_little_endian(self):
        from bleak.backends.scanner import AdvertisementData

        # article 0x3B1C = 15132 in little-endian: [0x1C, 0x3B]
        article = 0x3B1C
        raw = bytes([0x5E, 0x00, 0x00, 0x00, 0x1C, 0x3B])
        adv = AdvertisementData(
            local_name=None,
            manufacturer_data={0x00AB: raw},
            service_data={},
            service_uuids=[],
            platform_data=(),
            rssi=-60,
            tx_power=None,
        )
        key, art = JuraMachine._parse_advertisement(adv)
        assert key == 0x5E
        assert art == article


# ---------------------------------------------------------------------------
# _validate_brew_options
# ---------------------------------------------------------------------------


class TestValidateBrewOptions:
    @pytest.fixture
    def espresso_def(self):
        return MACHINES[_ARTICLE].products[Product.ESPRESSO]

    @pytest.fixture
    def milk_def(self):
        return MACHINES[_ARTICLE].products[Product.MILK_PORTION]

    def test_valid_options_no_error(self, espresso_def):
        JuraMachine._validate_brew_options(
            espresso_def,
            strength=4,
            water_ml=45,
            temperature=Temperature.HIGH,
            milk_ml=None,
            milk_break_ml=None,
        )

    def test_invalid_strength_raises(self, espresso_def):
        with pytest.raises(ValueError, match="strength"):
            JuraMachine._validate_brew_options(
                espresso_def,
                strength=0,
                water_ml=None,
                temperature=None,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_strength_on_product_without_strength_raises(self, milk_def):
        with pytest.raises(ValueError, match="strength"):
            JuraMachine._validate_brew_options(
                milk_def,
                strength=4,
                water_ml=None,
                temperature=None,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_water_below_min_raises(self, espresso_def):
        with pytest.raises(ValueError, match="water_ml"):
            JuraMachine._validate_brew_options(
                espresso_def,
                strength=None,
                water_ml=5,
                temperature=None,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_water_above_max_raises(self, espresso_def):
        with pytest.raises(ValueError, match="water_ml"):
            JuraMachine._validate_brew_options(
                espresso_def,
                strength=None,
                water_ml=200,
                temperature=None,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_water_on_product_without_water_raises(self, milk_def):
        with pytest.raises(ValueError, match="water"):
            JuraMachine._validate_brew_options(
                milk_def,
                strength=None,
                water_ml=50,
                temperature=None,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_invalid_temperature_raises(self, espresso_def):
        with pytest.raises(ValueError, match="temperature"):
            JuraMachine._validate_brew_options(
                espresso_def,
                strength=None,
                water_ml=None,
                temperature=Temperature.LOW,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_temperature_on_product_without_temperature_raises(self, milk_def):
        with pytest.raises(ValueError, match="temperature"):
            JuraMachine._validate_brew_options(
                milk_def,
                strength=None,
                water_ml=None,
                temperature=Temperature.NORMAL,
                milk_ml=None,
                milk_break_ml=None,
            )

    def test_milk_below_min_raises(self, espresso_def):
        # Espresso has no milk - wrong product for milk test; use cappuccino
        cappuccino = MACHINES[_ARTICLE].products[Product.CAPPUCCINO]
        with pytest.raises(ValueError, match="milk_ml"):
            JuraMachine._validate_brew_options(
                cappuccino,
                strength=None,
                water_ml=None,
                temperature=None,
                milk_ml=0,
                milk_break_ml=None,
            )


# ---------------------------------------------------------------------------
# _require_connected
# ---------------------------------------------------------------------------


class TestRequireConnected:
    def test_raises_when_not_connected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        with pytest.raises(MachineDisconnectedError):
            m._require_connected()

    def test_raises_when_client_disconnected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        mock_client = MagicMock()
        mock_client.is_connected = False
        m._client = mock_client
        m._machine_def = MACHINES[_ARTICLE]
        with pytest.raises(MachineDisconnectedError):
            m._require_connected()

    def test_returns_client_and_def_when_connected(self):
        m = _make_machine()
        client, machine_def = m._require_connected()
        assert client is m._client
        assert machine_def is m._machine_def


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    async def test_returns_machine_status(self):
        m = _make_machine()
        # All-zero encoded status → no alerts after decoding (encdec is symmetric)
        m._client.read_gatt_char.return_value = encdec(bytes(20), _KEY)
        status = await m.get_status()
        assert isinstance(status, MachineStatus)
        assert status.is_ready is True

    async def test_blocking_alert_makes_not_ready(self):
        m = _make_machine()
        # Encode raw data with bit 1 (fill_water, blocking) set
        raw = bytearray(20)
        raw[1] = 0b01000000  # bit 1 = MSB-1 of byte 1
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)
        status = await m.get_status()
        assert status.is_ready is False
        assert any(a.key == "fill_water" for a in status.alerts)

    async def test_non_blocking_alert_still_ready(self):
        m = _make_machine()
        # bit 12 = heating_up (non-blocking)
        # bit 12 → byte index = (12 >> 3) + 1 = 2, bit_offset = 7 - (12 & 7) = 3
        raw = bytearray(20)
        raw[2] = 1 << 3  # bit 12
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)
        status = await m.get_status()
        assert status.is_ready is True
        assert any(a.key == "heating_up" for a in status.alerts)


# ---------------------------------------------------------------------------
# brew
# ---------------------------------------------------------------------------


class TestBrew:
    async def test_brew_espresso_default(self):
        m = _make_machine()
        m._client.read_gatt_char.return_value = encdec(bytes(20), _KEY)
        await m.brew(Product.ESPRESSO)
        m._client.write_gatt_char.assert_called_once()

    async def test_brew_unsupported_product_raises(self):
        m = _make_machine()
        with pytest.raises(UnsupportedProductError):
            await m.brew(Product.CAFE_BARISTA)  # not in EF533

    async def test_brew_invalid_strength_raises(self):
        m = _make_machine()
        with pytest.raises(ValueError):
            await m.brew(Product.ESPRESSO, strength=99)

    async def test_brew_blocked_machine_raises(self):
        m = _make_machine()
        # Encode fill_water alert (bit 1) as active
        raw = bytearray(20)
        raw[1] = 0b01000000  # bit 1
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)
        with pytest.raises(MachineBlockedError) as exc_info:
            await m.brew(Product.ESPRESSO)
        assert any(a.key == "fill_water" for a in exc_info.value.alerts)

    async def test_brew_sends_to_correct_characteristic(self):
        from py_jura.protocol import START_PRODUCT_UUID

        m = _make_machine()
        m._client.read_gatt_char.return_value = encdec(bytes(20), _KEY)
        await m.brew(Product.ESPRESSO)
        call_args = m._client.write_gatt_char.call_args
        assert call_args[0][0] == START_PRODUCT_UUID

    async def test_brew_command_is_18_bytes(self):
        m = _make_machine()
        m._client.read_gatt_char.return_value = encdec(bytes(20), _KEY)
        await m.brew(Product.ESPRESSO)
        sent_data = m._client.write_gatt_char.call_args[0][1]
        assert len(sent_data) == 18


# ---------------------------------------------------------------------------
# lock / unlock / shutdown
# ---------------------------------------------------------------------------


class TestCommands:
    async def test_lock_writes_to_barista_uuid(self):
        from py_jura.protocol import BARISTA_MODE_UUID

        m = _make_machine()
        await m.lock()
        assert m._client.write_gatt_char.call_args[0][0] == BARISTA_MODE_UUID

    async def test_unlock_writes_to_barista_uuid(self):
        from py_jura.protocol import BARISTA_MODE_UUID

        m = _make_machine()
        await m.unlock()
        assert m._client.write_gatt_char.call_args[0][0] == BARISTA_MODE_UUID

    async def test_shutdown_writes_to_p_mode_uuid(self):
        from py_jura.protocol import P_MODE_UUID

        m = _make_machine()
        await m.shutdown()
        assert m._client.write_gatt_char.call_args[0][0] == P_MODE_UUID

    async def test_lock_raises_when_not_connected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        with pytest.raises(MachineDisconnectedError):
            await m.lock()


# ---------------------------------------------------------------------------
# _get_stat_val helper
# ---------------------------------------------------------------------------


class TestGetStatVal:
    def test_reads_first_slot(self):
        data = bytes([0x00, 0x00, 0x05, 0x00, 0x00, 0x0A])  # slot 0 = 5, slot 1 = 10
        assert _get_stat_val(data, offset=0, bytes_per_val=3) == 5

    def test_reads_second_slot(self):
        data = bytes([0x00, 0x00, 0x05, 0x00, 0x00, 0x0A])
        assert _get_stat_val(data, offset=1, bytes_per_val=3) == 10

    def test_big_endian_multi_byte(self):
        # 0x000186A0 = 100000
        data = bytes([0x00, 0x01, 0x86, 0xA0])
        assert _get_stat_val(data, offset=0, bytes_per_val=4) == 100000

    def test_returns_zero_if_out_of_bounds(self):
        data = bytes([0x01, 0x02])
        assert _get_stat_val(data, offset=5, bytes_per_val=3) == 0


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


class TestGetStats:
    def _make_stat_data(self, total: int, per_product: dict) -> bytes:
        """Build a raw (pre-encode) statistics data buffer."""
        # Slot 0 = total, slots indexed by product code
        max_code = max((0, *per_product.keys()))
        size = (max_code + 1) * 3
        buf = bytearray(size)

        def write_slot(slot: int, value: int) -> None:
            off = slot * 3
            buf[off] = (value >> 16) & 0xFF
            buf[off + 1] = (value >> 8) & 0xFF
            buf[off + 2] = value & 0xFF

        write_slot(0, total)
        for code, count in per_product.items():
            write_slot(code, count)
        return bytes(buf)

    async def test_returns_machine_stats(self):
        m = _make_machine()
        raw_data = self._make_stat_data(total=500, per_product={0x02: 42})
        m._client.read_gatt_char.return_value = encdec(raw_data, _KEY)

        with patch.object(m, "_poll_stats_ready"):
            stats = await m.get_stats()
        assert isinstance(stats, MachineStats)
        assert stats.total_count == 500
        assert stats.product_counts[Product.ESPRESSO] == 42

    async def test_raises_if_machine_never_ready(self):
        m = _make_machine()
        not_ready = encdec(bytes([0x00] * 20), _KEY)
        m._client.read_gatt_char.return_value = not_ready

        with patch("py_jura.machine.asyncio.sleep"):
            with pytest.raises(MachineDisconnectedError):
                await m.get_stats()

    async def test_skips_invalid_slots(self):
        m = _make_machine()
        raw_data = self._make_stat_data(total=10, per_product={0x02: 5, 0x04: 0xFFFF})
        m._client.read_gatt_char.return_value = encdec(raw_data, _KEY)

        with patch.object(m, "_poll_stats_ready"):
            stats = await m.get_stats()
        assert Product.ESPRESSO in stats.product_counts
        assert Product.CAPPUCCINO not in stats.product_counts

    async def test_writes_to_stats_command_uuid(self):
        from py_jura.protocol import STATISTICS_COMMAND_UUID

        m = _make_machine()
        raw_data = self._make_stat_data(total=0, per_product={})
        m._client.read_gatt_char.return_value = encdec(raw_data, _KEY)

        with patch.object(m, "_poll_stats_ready"):
            await m.get_stats()
        write_call = m._client.write_gatt_char.call_args
        assert write_call[0][0] == STATISTICS_COMMAND_UUID


# ---------------------------------------------------------------------------
# cancel_brew
# ---------------------------------------------------------------------------


class TestCancelBrew:
    async def test_writes_to_update_product_uuid(self):
        from py_jura.protocol import UPDATE_PRODUCT_UUID

        m = _make_machine()
        await m.cancel_brew()
        assert m._client.write_gatt_char.call_args[0][0] == UPDATE_PRODUCT_UUID

    async def test_cancel_command_has_0xff_second_byte(self):
        from py_jura.encoder import encdec

        m = _make_machine()
        await m.cancel_brew()
        sent = m._client.write_gatt_char.call_args[0][1]
        decoded = encdec(bytes(sent), _KEY)
        assert decoded[1] == 0xFF

    async def test_raises_when_not_connected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        with pytest.raises(MachineDisconnectedError):
            await m.cancel_brew()


# ---------------------------------------------------------------------------
# get_daily_stats
# ---------------------------------------------------------------------------


class TestGetDailyStats:
    def _make_stat_data(self, total: int, per_product: dict) -> bytes:
        max_code = max((0, *per_product.keys()))
        size = (max_code + 1) * 3
        buf = bytearray(size)

        def write_slot(slot: int, value: int) -> None:
            off = slot * 3
            buf[off] = (value >> 16) & 0xFF
            buf[off + 1] = (value >> 8) & 0xFF
            buf[off + 2] = value & 0xFF

        write_slot(0, total)
        for code, count in per_product.items():
            write_slot(code, count)
        return bytes(buf)

    async def test_returns_machine_stats(self):
        from py_jura.models import MachineStats

        m = _make_machine()
        raw_data = self._make_stat_data(total=7, per_product={0x02: 3})
        m._client.read_gatt_char.return_value = encdec(raw_data, _KEY)

        with patch.object(m, "_poll_stats_ready"):
            stats = await m.get_daily_stats()
        assert isinstance(stats, MachineStats)
        assert stats.total_count == 7
        assert stats.product_counts[Product.ESPRESSO] == 3

    async def test_uses_daily_counters_mode(self):
        from py_jura.encoder import encdec as _enc
        from py_jura.protocol import STATISTICS_COMMAND_UUID, StatMode

        m = _make_machine()
        raw_data = self._make_stat_data(total=0, per_product={})
        m._client.read_gatt_char.return_value = encdec(raw_data, _KEY)

        with patch.object(m, "_poll_stats_ready"):
            await m.get_daily_stats()
        write_call = m._client.write_gatt_char.call_args
        assert write_call[0][0] == STATISTICS_COMMAND_UUID
        # Verify mode byte: decoded[2] should be 16 (DAILY_COUNTERS)
        sent = write_call[0][1]
        decoded = _enc(bytes(sent), _KEY)
        assert decoded[2] == int(StatMode.DAILY_COUNTERS)


# ---------------------------------------------------------------------------
# get_about
# ---------------------------------------------------------------------------


class TestGetAbout:
    def _make_about_data(self, bluefrog: str, machine: str) -> bytes:
        """Build a 51-byte ABOUT_MACHINE payload with version strings at bytes 27-34, 35-50."""
        buf = bytearray(51)
        for i, ch in enumerate(bluefrog[:8]):
            buf[27 + i] = ord(ch)
        for i, ch in enumerate(machine[:16]):
            buf[35 + i] = ord(ch)
        return bytes(buf)

    async def test_returns_machine_info(self):
        from py_jura.models import MachineInfo

        m = _make_machine()
        # ABOUT_MACHINE is plaintext - returned raw, not encoded
        raw = self._make_about_data("V1.2.3", "FW4.5.6")
        m._client.read_gatt_char.return_value = raw

        info = await m.get_about()
        assert isinstance(info, MachineInfo)
        assert info.bluefrog_version == "V1.2.3"
        assert info.machine_version == "FW4.5.6"

    async def test_reads_from_about_machine_uuid(self):
        from py_jura.protocol import ABOUT_MACHINE_UUID

        m = _make_machine()
        m._client.read_gatt_char.return_value = bytes(51)

        await m.get_about()
        assert m._client.read_gatt_char.call_args[0][0] == ABOUT_MACHINE_UUID

    async def test_skips_null_bytes(self):
        m = _make_machine()
        # Embed "AB\x00CD" at bluefrog position - null should be stripped
        buf = bytearray(51)
        buf[27:32] = b"AB\x00CD"
        m._client.read_gatt_char.return_value = bytes(buf)

        info = await m.get_about()
        assert "\x00" not in info.bluefrog_version
        assert info.bluefrog_version == "ABCD"

    async def test_raises_when_not_connected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        with pytest.raises(MachineDisconnectedError):
            await m.get_about()


# ---------------------------------------------------------------------------
# get_progress
# ---------------------------------------------------------------------------


class TestGetProgress:
    async def test_returns_brew_progress(self):
        from py_jura.models import BrewProgress

        m = _make_machine()
        raw = bytearray(20)
        raw[0] = _KEY  # session key marker (always byte[0])
        raw[1] = 0x39  # brew_starting
        raw[2] = 0x02  # ESPRESSO
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)

        progress = await m.get_progress()
        assert isinstance(progress, BrewProgress)
        assert progress.state == 0x39
        assert progress.product_code == 0x02

    async def test_is_idle_when_state_zero(self):
        m = _make_machine()
        raw = bytearray(20)
        raw[0] = _KEY
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)

        progress = await m.get_progress()
        assert progress.is_idle is True

    async def test_is_idle_when_state_is_key(self):
        # byte[1]=key means BLE-connected with no active brew (key in state slot = P_MODE idle)
        m = _make_machine()
        data = bytearray(20)
        data[0] = _KEY
        data[1] = _KEY
        m._client.read_gatt_char.return_value = encdec(bytes(data), _KEY)

        progress = await m.get_progress()
        assert progress.is_idle is True

    async def test_is_done_when_state_enjoy(self):
        m = _make_machine()
        raw = bytearray(20)
        raw[0] = _KEY
        raw[1] = 0x3E  # enjoy/done
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)

        progress = await m.get_progress()
        assert progress.is_done is True

    async def test_product_property_resolves_enum(self):
        m = _make_machine()
        raw = bytearray(20)
        raw[0] = _KEY
        raw[1] = 0x3C  # dispensing
        raw[2] = Product.ESPRESSO.value
        m._client.read_gatt_char.return_value = encdec(bytes(raw), _KEY)

        progress = await m.get_progress()
        assert progress.product is Product.ESPRESSO

    async def test_reads_from_product_progress_uuid(self):
        from py_jura.protocol import PRODUCT_PROGRESS_UUID

        m = _make_machine()
        m._client.read_gatt_char.return_value = encdec(bytes(20), _KEY)

        await m.get_progress()
        assert m._client.read_gatt_char.call_args[0][0] == PRODUCT_PROGRESS_UUID

    async def test_raises_when_not_connected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        with pytest.raises(MachineDisconnectedError):
            await m.get_progress()


# ---------------------------------------------------------------------------
# get_maintenance
# ---------------------------------------------------------------------------


class TestGetMaintenance:
    def _make_counter_data(self, slots: list[int]) -> bytes:
        """Build maintenance counter buffer: 2 bytes per slot, big-endian."""
        buf = bytearray(len(slots) * 2)
        for i, val in enumerate(slots):
            buf[i * 2] = (val >> 8) & 0xFF
            buf[i * 2 + 1] = val & 0xFF
        return bytes(buf)

    def _make_percent_data(self, slots: list[int]) -> bytes:
        """Build maintenance percent buffer: 1 byte per slot."""
        return bytes(slots)

    async def test_returns_maintenance_stats(self):
        from py_jura.models import MaintenanceStats

        m = _make_machine()
        # 6 counter slots: cleaning=10, filter_change=2, decalc=3, cappu_rinse=4, coffee_rinse=5, cappu_clean=6
        counter_raw = self._make_counter_data([10, 2, 3, 4, 5, 6])
        # 3 percent slots: cleaning=45, filter_change=80, decalc=20
        percent_raw = self._make_percent_data([45, 80, 20])
        m._client.read_gatt_char.side_effect = [encdec(counter_raw, _KEY), encdec(percent_raw, _KEY)]

        with patch.object(m, "_poll_stats_ready"):
            stats = await m.get_maintenance()
        assert isinstance(stats, MaintenanceStats)
        assert stats.counters["cleaning"] == 10
        assert stats.counters["decalc"] == 3
        assert stats.percentages["cleaning"] == 45
        assert stats.percentages["filter_change"] == 80
        assert stats.percentages["decalc"] == 20

    async def test_counter_keys_match_machine_def(self):
        from py_jura.machines import MACHINES

        m = _make_machine()
        machine_def = MACHINES[_ARTICLE]
        counter_raw = self._make_counter_data([0] * len(machine_def.maintenance_counter_types))
        percent_raw = self._make_percent_data([0] * len(machine_def.maintenance_percent_types))
        m._client.read_gatt_char.side_effect = [encdec(counter_raw, _KEY), encdec(percent_raw, _KEY)]

        with patch.object(m, "_poll_stats_ready"):
            stats = await m.get_maintenance()
        assert set(stats.counters.keys()) == set(machine_def.maintenance_counter_types)
        assert set(stats.percentages.keys()) == set(machine_def.maintenance_percent_types)

    async def test_raises_when_not_connected(self):
        m = JuraMachine("AA:BB:CC:DD:EE:FF")
        with pytest.raises(MachineDisconnectedError):
            await m.get_maintenance()
