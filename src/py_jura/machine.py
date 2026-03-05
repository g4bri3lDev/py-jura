"""
JuraMachine - async context manager for JURA coffee machines over BLE.

Usage:
    async with JuraMachine("XX:XX:XX:XX:XX:XX") as machine:
        status = await machine.get_status()
        await machine.brew(Product.ESPRESSO, strength=6, water_ml=40)
"""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient

from py_jura._connection import _JuraConnection
from py_jura.encoder import encdec
from py_jura.exceptions import MachineBlockedError, MachineDisconnectedError, UnsupportedProductError
from py_jura.machines import ARTICLE_NAMES
from py_jura.models import BrewProgress, MachineInfo, MachineStats, MachineStatus, MaintenanceStats
from py_jura.products import Product, ProductDefinition, Temperature
from py_jura.protocol import (
    ABOUT_MACHINE_UUID,
    BARISTA_MODE_UUID,
    MACHINE_STATUS_UUID,
    P_MODE_UUID,
    PRODUCT_PROGRESS_UUID,
    START_PRODUCT_UUID,
    STATISTICS_COMMAND_UUID,
    STATISTICS_DATA_UUID,
    UPDATE_PRODUCT_UUID,
    StatMode,
    build_brew_command,
    build_cancel_brew_command,
    build_lock_command,
    build_shutdown_command,
    build_stats_command,
    build_unlock_command,
    parse_alert_bits,
)

_LOGGER = logging.getLogger(__name__)


def _get_stat_val(data: bytes, offset: int, bytes_per_val: int) -> int:
    """Read a big-endian integer from `data` at `offset * bytes_per_val`."""
    start = offset * bytes_per_val
    if len(data) < start + bytes_per_val:
        return 0
    result = 0
    for i in range(bytes_per_val):
        result = (result << 8) | data[start + i]
    return result


class JuraMachine(_JuraConnection):
    """
    Async context manager for a JURA coffee machine over BLE.

    Parameters
    ----------
    address:
        BLE address of the machine (e.g. "AA:BB:CC:DD:EE:FF" on Linux/Windows
        or a UUID string on macOS).
    max_retries:
        Number of reconnection attempts before raising MachineDisconnectedError.
    """

    async def __aenter__(self) -> JuraMachine:
        await self._connect()
        return self

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def address(self) -> str:
        """BLE address of the machine."""
        return self._address

    @property
    def article_number(self) -> int:
        """Article number parsed from the BLE advertisement. Identifies the exact machine variant."""
        if self._article_number is None:
            raise MachineDisconnectedError("Not connected.")
        return self._article_number

    @property
    def display_name(self) -> str:
        """Customer-facing model name (e.g. 'E8', 'GIGA X8') for this article number."""
        return ARTICLE_NAMES[self.article_number]

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    async def get_status(self) -> MachineStatus:
        """
        Read MACHINE_STATUS and return a MachineStatus with active alerts.

        The status is decoded with the machine's key and all active alert bits
        are looked up in the machine definition's alert table.
        """
        client, machine_def = self._require_connected()
        data = await client.read_gatt_char(MACHINE_STATUS_UUID)
        active_bits = parse_alert_bits(bytes(data), self._key)
        alerts = [a for bit in active_bits if (a := machine_def.alerts.get(bit)) is not None]
        return MachineStatus(alerts=alerts)

    async def get_progress(self) -> BrewProgress:
        """
        Read the current brewing state from the PRODUCT_PROGRESS characteristic.

        Returns a BrewProgress with:
          - state: raw state code (0x00=idle, 0x21=heating, 0x24=coffee_ready, 0x3E=enjoy)
          - product_code: active product code (0 when idle)
        """
        client, _ = self._require_connected()
        raw = bytes(await client.read_gatt_char(PRODUCT_PROGRESS_UUID))
        data = encdec(raw, self._key)
        # byte[0] = session key (marker), byte[1] = state, byte[2] = product code
        return BrewProgress(state=data[1], product_code=data[2])

    async def get_about(self) -> MachineInfo:
        """
        Read firmware version strings from the ABOUT_MACHINE characteristic.

        Returns a MachineInfo with:
          - bluefrog_version: BLE module (BlueFrog) firmware version string
          - machine_version: Coffee machine firmware version string
        """
        client, _ = self._require_connected()
        raw = bytes(await client.read_gatt_char(ABOUT_MACHINE_UUID))
        # ABOUT_MACHINE is plaintext - not XOR-encoded like command characteristics

        def _ascii_slice(b: bytes, start: int, end: int) -> str:
            return bytes(x for x in b[start:end] if x != 0).decode("ascii", errors="replace")

        return MachineInfo(
            bluefrog_version=_ascii_slice(raw, 27, 35),
            machine_version=_ascii_slice(raw, 35, 51),
        )

    # ------------------------------------------------------------------
    # Brew
    # ------------------------------------------------------------------

    async def brew(
        self,
        product: Product,
        strength: int | None = None,
        water_ml: int | None = None,
        temperature: Temperature | None = None,
        milk_ml: int | None = None,
        milk_break_ml: int | None = None,
    ) -> None:
        """
        Brew a product.

        Parameters
        ----------
        product:
            The drink to brew.
        strength:
            Strength level (must be in the product's valid values).
        water_ml:
            Water amount in ml (must be within the product's min/max range).
        temperature:
            Brew temperature (must be in the product's valid options).
        milk_ml:
            Milk amount in ml (must be within the product's min/max range).
        milk_break_ml:
            Milk break duration in ml-equivalent (must be within product's range).

        Raises
        ------
        UnsupportedProductError
            If the product is not available on this machine.
        ValueError
            If any option value is out of range or invalid.
        MachineBlockedError
            If the machine has active blocking alerts.
        MachineDisconnectedError
            If not connected.
        """
        client, machine_def = self._require_connected()

        product_def = machine_def.products.get(product)
        if product_def is None:
            raise UnsupportedProductError(f"{product.name} is not available on {machine_def.name}.")

        self._validate_brew_options(product_def, strength, water_ml, temperature, milk_ml, milk_break_ml)

        status = await self.get_status()
        if not status.is_ready:
            blocking = [a for a in status.alerts if a.blocking]
            raise MachineBlockedError(blocking)

        cmd = build_brew_command(
            product_def,
            self._key,
            strength=strength,
            water_ml=water_ml,
            temperature=temperature,
            milk_ml=milk_ml,
            milk_break_ml=milk_break_ml,
        )
        await client.write_gatt_char(START_PRODUCT_UUID, cmd, response=True)
        _LOGGER.info("Brew command sent: %s", product.name)

    async def cancel_brew(self) -> None:
        """Cancel the currently in-progress brew."""
        client, _ = self._require_connected()
        cmd = build_cancel_brew_command(self._key)
        await client.write_gatt_char(UPDATE_PRODUCT_UUID, cmd, response=True)
        _LOGGER.info("Cancel brew command sent to %s", self._address)

    @staticmethod
    def _validate_brew_options(
        product_def: ProductDefinition,
        strength: int | None,
        water_ml: int | None,
        temperature: Temperature | None,
        milk_ml: int | None,
        milk_break_ml: int | None,
    ) -> None:
        if strength is not None:
            if product_def.strength is None:
                raise ValueError(f"{product_def.name} does not support a strength setting.")
            if strength not in product_def.strength.values:
                raise ValueError(f"Invalid strength {strength}. Valid values: {product_def.strength.values}.")

        if water_ml is not None:
            if product_def.water is None:
                raise ValueError(f"{product_def.name} does not support a water amount setting.")
            r = product_def.water
            if not r.min <= water_ml <= r.max:
                raise ValueError(f"water_ml={water_ml} out of range [{r.min}, {r.max}].")

        if temperature is not None:
            if product_def.temperature is None:
                raise ValueError(f"{product_def.name} does not support a temperature setting.")
            if temperature not in product_def.temperature.options:
                raise ValueError(
                    f"Invalid temperature {temperature}. Valid options: {product_def.temperature.options}."
                )

        if milk_ml is not None:
            if product_def.milk is None:
                raise ValueError(f"{product_def.name} does not support a milk amount setting.")
            r = product_def.milk
            if not r.min <= milk_ml <= r.max:
                raise ValueError(f"milk_ml={milk_ml} out of range [{r.min}, {r.max}].")

        if milk_break_ml is not None:
            if product_def.milk_break is None:
                raise ValueError(f"{product_def.name} does not support a milk break setting.")
            r = product_def.milk_break
            if not r.min <= milk_break_ml <= r.max:
                raise ValueError(f"milk_break_ml={milk_break_ml} out of range [{r.min}, {r.max}].")

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    async def _poll_stats_ready(self, client: BleakClient) -> None:
        """Poll STATISTICS_COMMAND_UUID until the machine signals it has processed the command.

        The machine clears the ready signal (decoded[0] != key) while processing,
        then sets it again (decoded[0] == key) when the data is ready to read.
        Waiting for the cleared state first ensures we don't read stale data from
        a previous command.
        """
        # Phase 1: wait for not-ready (machine starts processing new command)
        for _ in range(20):
            await asyncio.sleep(0.1)
            raw = bytes(await client.read_gatt_char(STATISTICS_COMMAND_UUID))
            if encdec(raw, self._key)[0] != self._key:
                break

        # Phase 2: wait for ready (machine finished, data available)
        for _ in range(40):
            await asyncio.sleep(0.25)
            raw = bytes(await client.read_gatt_char(STATISTICS_COMMAND_UUID))
            if encdec(raw, self._key)[0] == self._key:
                return
        raise MachineDisconnectedError("Machine did not respond to statistics request within 10 seconds.")

    async def _get_product_counter_stats(self, mode: StatMode) -> MachineStats:
        """Send a product-counter stats request and return parsed MachineStats."""
        client, machine_def = self._require_connected()

        cmd = build_stats_command(self._key, mode)
        await client.write_gatt_char(STATISTICS_COMMAND_UUID, cmd, response=True)
        await self._poll_stats_ready(client)

        raw_data = bytes(await client.read_gatt_char(STATISTICS_DATA_UUID))
        data = encdec(raw_data, self._key)

        total_count = _get_stat_val(data, offset=0, bytes_per_val=3)

        product_counts: dict[Product, int] = {}
        for product in machine_def.products:
            code = product.value
            count = _get_stat_val(data, offset=code, bytes_per_val=3)
            if count != 0xFFFF:
                product_counts[product] = count

        return MachineStats(total_count=total_count, product_counts=product_counts)

    async def get_stats(self) -> MachineStats:
        """Read total and per-product brew counts from the machine."""
        return await self._get_product_counter_stats(StatMode.PRODUCT_COUNTERS)

    async def get_daily_stats(self) -> MachineStats:
        """Read today's brew counts from the machine."""
        return await self._get_product_counter_stats(StatMode.DAILY_COUNTERS)

    async def get_maintenance(self) -> MaintenanceStats:
        """
        Read maintenance counters and wear percentages from the machine.

        Issues two separate statistics requests:
          - MAINTENANCE_COUNTER (mode=4): 2 bytes/slot, big-endian
          - MAINTENANCE_PERCENT (mode=8): 1 byte/slot

        Returns a MaintenanceStats keyed by the machine's maintenance type names.
        """
        client, machine_def = self._require_connected()

        cmd = build_stats_command(self._key, StatMode.MAINTENANCE_COUNTER)
        await client.write_gatt_char(STATISTICS_COMMAND_UUID, cmd, response=True)
        await self._poll_stats_ready(client)

        raw_data = bytes(await client.read_gatt_char(STATISTICS_DATA_UUID))
        counter_data = encdec(raw_data, self._key)

        counters: dict[str, int] = {}
        for i, name in enumerate(machine_def.maintenance_counter_types):
            counters[name] = _get_stat_val(counter_data, offset=i, bytes_per_val=2)

        cmd = build_stats_command(self._key, StatMode.MAINTENANCE_PERCENT)
        await client.write_gatt_char(STATISTICS_COMMAND_UUID, cmd, response=True)
        await self._poll_stats_ready(client)

        raw_data = bytes(await client.read_gatt_char(STATISTICS_DATA_UUID))
        percent_data = encdec(raw_data, self._key)

        percentages: dict[str, int] = {}
        for i, name in enumerate(machine_def.maintenance_percent_types):
            percentages[name] = _get_stat_val(percent_data, offset=i, bytes_per_val=1)

        return MaintenanceStats(counters=counters, percentages=percentages)

    # ------------------------------------------------------------------
    # Machine control
    # ------------------------------------------------------------------

    async def lock(self) -> None:
        """Lock the machine's touchscreen (Barista mode)."""
        client, _ = self._require_connected()
        await client.write_gatt_char(BARISTA_MODE_UUID, build_lock_command(self._key), response=True)

    async def unlock(self) -> None:
        """Unlock the machine's touchscreen (Barista mode)."""
        client, _ = self._require_connected()
        await client.write_gatt_char(BARISTA_MODE_UUID, build_unlock_command(self._key), response=True)

    async def shutdown(self) -> None:
        """Send the machine shutdown command."""
        client, _ = self._require_connected()
        await client.write_gatt_char(P_MODE_UUID, build_shutdown_command(self._key), response=True)
        _LOGGER.info("Shutdown command sent to %s", self._address)
