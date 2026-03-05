"""Exceptions raised by py-jura."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_jura.models import Alert


class JuraError(Exception):
    """Base exception for all py-jura errors."""


class MachineNotFoundError(JuraError):
    """Raised when the machine cannot be found via BLE scan."""


class MachineDisconnectedError(JuraError):
    """Raised when the machine disconnects and reconnect attempts are exhausted."""


class MachineBlockedError(JuraError):
    """Raised when the machine has active blocking alerts and cannot brew."""

    def __init__(self, alerts: list[Alert]) -> None:
        self.alerts = alerts
        names = ", ".join(a.key for a in alerts)
        super().__init__(f"Machine blocked by: {names}")


class UnsupportedProductError(JuraError):
    """Raised when the requested product is not supported by this machine."""
