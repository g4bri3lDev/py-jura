"""Tests for py-jura exceptions."""

from py_jura.exceptions import (
    JuraError,
    MachineBlockedError,
    MachineDisconnectedError,
    MachineNotFoundError,
    UnsupportedProductError,
)


def test_hierarchy():
    assert issubclass(MachineNotFoundError, JuraError)
    assert issubclass(MachineDisconnectedError, JuraError)
    assert issubclass(MachineBlockedError, JuraError)
    assert issubclass(UnsupportedProductError, JuraError)


def test_machine_blocked_error_stores_alerts():
    from dataclasses import dataclass

    @dataclass
    class FakeAlert:
        key: str

    alerts = [FakeAlert("fill_water"), FakeAlert("empty_grounds")]
    err = MachineBlockedError(alerts)
    assert err.alerts == alerts


def test_machine_blocked_error_message():
    from dataclasses import dataclass

    @dataclass
    class FakeAlert:
        key: str

    alerts = [FakeAlert("fill_water"), FakeAlert("empty_grounds")]
    err = MachineBlockedError(alerts)
    assert "fill_water" in str(err)
    assert "empty_grounds" in str(err)
