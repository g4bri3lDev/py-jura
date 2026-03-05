"""Tests for py-jura data models."""

import pytest

from py_jura.models import Alert, MachineStatus


class TestAlert:
    def test_blocking(self):
        a = Alert(bit=1, key="fill_water", blocking=True)
        assert a.blocking is True

    def test_non_blocking(self):
        a = Alert(bit=12, key="heating_up", blocking=False)
        assert a.blocking is False

    def test_frozen(self):
        a = Alert(bit=1, key="fill_water", blocking=True)
        with pytest.raises(Exception):
            a.key = "other"  # type: ignore[misc]


class TestMachineStatus:
    def test_ready_when_no_alerts(self):
        assert MachineStatus(alerts=[]).is_ready is True

    def test_ready_when_only_non_blocking_alerts(self):
        alerts = [Alert(bit=12, key="heating_up", blocking=False)]
        assert MachineStatus(alerts=alerts).is_ready is True

    def test_not_ready_when_blocking_alert(self):
        alerts = [Alert(bit=1, key="fill_water", blocking=True)]
        assert MachineStatus(alerts=alerts).is_ready is False

    def test_not_ready_when_mixed_alerts(self):
        alerts = [
            Alert(bit=12, key="heating_up", blocking=False),
            Alert(bit=1, key="fill_water", blocking=True),
        ]
        assert MachineStatus(alerts=alerts).is_ready is False

    def test_frozen(self):
        status = MachineStatus(alerts=[])
        with pytest.raises(Exception):
            status.alerts = []  # type: ignore[misc]
