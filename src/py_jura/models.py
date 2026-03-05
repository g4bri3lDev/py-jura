"""Data models for py-jura."""

from __future__ import annotations

from dataclasses import dataclass, field

from py_jura.products import Product


@dataclass(frozen=True)
class Alert:
    """A machine alert decoded from the MACHINE_STATUS characteristic."""

    bit: int
    key: str  # snake_case identifier e.g. "fill_water"
    blocking: bool  # True = machine will not brew until resolved


@dataclass(frozen=True)
class MachineStatus:
    """Current status snapshot of the coffee machine."""

    alerts: list[Alert]

    @property
    def is_ready(self) -> bool:
        """True when no blocking alerts are active."""
        return not any(a.blocking for a in self.alerts)


@dataclass(frozen=True)
class MachineStats:
    """
    Product brew counts read from the STATISTICS_DATA characteristic.

    Attributes
    ----------
    total_count:
        Total number of products brewed across all types (slot 0 in the data).
    product_counts:
        Maps each Product enum member to its individual brew count.
        Products with no recorded brews are omitted.
    """

    total_count: int
    product_counts: dict[Product, int] = field(default_factory=dict)


@dataclass(frozen=True)
class MachineInfo:
    """Firmware version strings from the ABOUT_MACHINE characteristic."""

    bluefrog_version: str  # BlueFrog (BLE module) firmware version
    machine_version: str  # Coffee machine firmware version


@dataclass(frozen=True)
class MaintenanceStats:
    """
    Maintenance counters and wear percentages from the STATISTICS characteristics.

    Both dicts are keyed by maintenance type name (e.g. "cleaning", "decalc").
    Type names and their order are defined in the machine's MachineDefinition.
    """

    counters: dict[str, int]  # number of times each maintenance was performed
    percentages: dict[str, int]  # remaining capacity 0–100; 0 = service overdue, 100 = just serviced


# State codes that indicate an active brewing or alert process.
# Any other value (including 0x00 = true idle) is treated as idle.
_BREW_ACTIVE_STATES: frozenset[int] = frozenset({0x0E, 0x21, 0x24, 0x25, 0x39, 0x3C, 0x3E})


@dataclass(frozen=True)
class BrewProgress:
    """
    Real-time brewing state from the PRODUCT_PROGRESS characteristic.

    Attributes
    ----------
    state:
        Raw state code from decoded byte[1].  Confirmed values on EF533:
        0x00=idle, 0x39=brew_starting, 0x3C=dispensing, 0x3E=enjoy/done
    product_code:
        Raw product code from decoded byte[2].  0 when no product is active.
    """

    state: int
    product_code: int

    @property
    def description(self) -> str:
        """Human-readable description of the current state."""
        labels: dict[int, str] = {
            0x00: "Idle",
            0x39: "Starting",
            0x3C: "Brewing",
            0x3E: "Done",
        }
        return labels.get(self.state, f"Unknown (0x{self.state:02X})")

    @property
    def is_idle(self) -> bool:
        """True when the machine has no active brew or alert process."""
        return self.state not in _BREW_ACTIVE_STATES

    @property
    def is_done(self) -> bool:
        """True when the product is ready or in the cup (Coffee Ready or Enjoy)."""
        return self.state in (0x24, 0x3E)

    @property
    def product(self) -> Product | None:
        """The active Product enum member, or None if the code is unrecognised."""
        try:
            return Product(self.product_code)
        except ValueError:
            return None
