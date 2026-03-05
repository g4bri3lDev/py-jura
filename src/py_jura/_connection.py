"""
BLE connection lifecycle for JuraMachine.

This module is internal - import JuraMachine from py_jura.machine instead.
"""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak_retry_connector import establish_connection

from py_jura.exceptions import MachineDisconnectedError, MachineNotFoundError
from py_jura.machines import MACHINES, MachineDefinition
from py_jura.protocol import (
    P_MODE_UUID,
    build_disconnect_command,
    build_heartbeat_command,
)

_LOGGER = logging.getLogger(__name__)
_HEARTBEAT_INTERVAL = 9  # seconds between heartbeat write to P_MODE


class _JuraConnection:
    """
    BLE connection lifecycle mixin for JuraMachine.

    Handles scanning, connecting, heartbeating, and reconnecting.
    All states are stored on `self` and shared with the JuraMachine subclass.
    """

    def __init__(self, address: str, max_retries: int = 3) -> None:
        self._address = address
        self._max_retries = max_retries

        self._key: int = 0
        self._article_number: int | None = None
        self._machine_def: MachineDefinition | None = None
        self._client: BleakClient | None = None
        self._ble_device: BLEDevice | None = None

        self._heartbeat_task: asyncio.Task[None] | None = None
        self._stop_heartbeat = asyncio.Event()
        self._disconnecting = False

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> _JuraConnection:
        await self._connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._disconnect()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def _connect(self) -> None:
        """Scan for the device, parse advertisement, establish BLE connection."""
        _LOGGER.debug("Scanning for JURA machine at %s", self._address)
        device, adv = await self._scan()

        self._ble_device = device
        self._key, article_number = self._parse_advertisement(adv)
        self._article_number = article_number

        machine_def = MACHINES.get(article_number)
        if machine_def is None:
            raise MachineNotFoundError(
                f"Unknown article number {article_number} (address: {self._address}). "
                "The machine model is not supported."
            )
        self._machine_def = machine_def
        _LOGGER.debug(
            "Identified %s (article %d), key=0x%02X",
            machine_def.name,
            article_number,
            self._key,
        )

        self._client = await establish_connection(
            BleakClient,
            device,
            device.name or self._address,
            disconnected_callback=self._on_disconnect,
        )
        _LOGGER.debug("Connected to %s", self._address)

        self._stop_heartbeat.clear()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_run())

    async def _disconnect(self) -> None:
        """Send a graceful disconnect command, stop heartbeat, close BLE."""
        self._disconnecting = True

        if self._heartbeat_task is not None:
            self._stop_heartbeat.set()
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        if self._client and self._client.is_connected:
            try:
                cmd = build_disconnect_command(self._key)
                await self._client.write_gatt_char(P_MODE_UUID, cmd, response=False)
            except Exception:
                pass  # best-effort; proceed with BLE disconnect regardless
            await self._client.disconnect()
            _LOGGER.debug("Disconnected from %s", self._address)

        self._disconnecting = False

    def _on_disconnect(self, _client: BleakClient) -> None:
        """Called by bleak on unexpected disconnection."""
        if not self._disconnecting:
            _LOGGER.warning("Unexpected disconnection from %s", self._address)
            self._stop_heartbeat.set()

    # ------------------------------------------------------------------
    # Scanning and advertisement parsing
    # ------------------------------------------------------------------

    async def _scan(self) -> tuple[BLEDevice, AdvertisementData]:
        """Scan BLE and return (BLEDevice, AdvertisementData) for our address."""
        found: list[tuple[BLEDevice, AdvertisementData]] = []

        def callback(device: BLEDevice, adv: AdvertisementData) -> None:
            if device.address.upper() == self._address.upper():
                found.append((device, adv))

        async with BleakScanner(detection_callback=callback):
            for _ in range(100):
                if found:
                    break
                await asyncio.sleep(0.1)

        if not found:
            raise MachineNotFoundError(f"JURA machine not found at {self._address} after 10 seconds of scanning.")

        return found[-1]

    @staticmethod
    def _parse_advertisement(adv: AdvertisementData) -> tuple[int, int]:
        """
        Extract key and article number from BLE manufacturer data.

        Format (JURA-specific, at least 6 bytes):
          byte[0]: encryption key
          bytes[1:4]: unknown
          bytes[4:6]: article number, little-endian

        Returns (key, article_number).
        """
        for data in adv.manufacturer_data.values():
            if len(data) >= 6:
                key = data[0]
                article_number = int.from_bytes(data[4:6], byteorder="little")
                return key, article_number

        raise MachineNotFoundError(
            "JURA advertisement data missing or too short - could not extract encryption key and article number."
        )

    # ------------------------------------------------------------------
    # Heartbeat + reconnection
    # ------------------------------------------------------------------

    async def _heartbeat_run(self) -> None:
        """Send a heartbeat every 9 s to stay in BLE mode. Reconnects on a drop."""
        while True:
            try:
                await asyncio.wait_for(
                    asyncio.shield(asyncio.ensure_future(self._stop_heartbeat.wait())),
                    timeout=_HEARTBEAT_INTERVAL,
                )
            except asyncio.TimeoutError:
                pass  # normal; send heartbeat

            if self._stop_heartbeat.is_set() and self._disconnecting:
                return  # clean shutdown requested

            if self._stop_heartbeat.is_set():
                self._stop_heartbeat.clear()
                try:
                    await self._reconnect_with_backoff()
                except MachineDisconnectedError:
                    _LOGGER.error("Failed to reconnect to %s", self._address)
                    return
                continue

            if self._client and self._client.is_connected:
                try:
                    cmd = build_heartbeat_command(self._key)
                    await self._client.write_gatt_char(P_MODE_UUID, cmd, response=False)
                    _LOGGER.debug("Heartbeat sent to %s", self._address)
                except Exception as exc:
                    _LOGGER.warning("Heartbeat failed: %s", exc)

    async def _reconnect_with_backoff(self) -> None:
        """Reconnect with exponential backoff up to max_retries."""
        assert self._ble_device is not None

        for attempt in range(self._max_retries):
            delay = 2**attempt
            _LOGGER.info(
                "Reconnect attempt %d/%d in %ds…",
                attempt + 1,
                self._max_retries,
                delay,
            )
            await asyncio.sleep(delay)
            try:
                self._client = await establish_connection(
                    BleakClient,
                    self._ble_device,
                    self._ble_device.name or self._address,
                    disconnected_callback=self._on_disconnect,
                )
                _LOGGER.info("Reconnected to %s", self._address)
                return
            except Exception as exc:
                _LOGGER.warning("Reconnect attempt %d failed: %s", attempt + 1, exc)

        raise MachineDisconnectedError(f"Failed to reconnect to {self._address} after {self._max_retries} attempts.")

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def _require_connected(self) -> tuple[BleakClient, MachineDefinition]:
        """Return (client, machine_def), raising MachineDisconnectedError if not connected."""
        if self._client is None or not self._client.is_connected:
            raise MachineDisconnectedError(
                f"Not connected to {self._address}. Use 'async with JuraMachine(...)' first."
            )
        if self._machine_def is None:
            raise MachineDisconnectedError("Machine definition not loaded.")
        return self._client, self._machine_def
