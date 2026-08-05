"""Tests for como.battery — per-platform battery data collection."""

from __future__ import annotations

import json
import plistlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from como.battery import (
    BatteryInfo,
    _aggregate,
    _get_batteries_linux,
    _get_batteries_macos,
    _get_battery_windows,
    get_batteries,
    get_battery,
)

# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------

_MACOS_CHARGING = [
    {
        "BatterySerialNumber": "ABC123",
        "MaxCapacity": 5000,
        "CurrentCapacity": 4000,
        "DesignCapacity": 5500,
        "CycleCount": 42,
        "Voltage": 12000,
        "Amperage": 1500,
    }
]

_MACOS_DISCHARGING = [
    {
        **_MACOS_CHARGING[0],
        # ioreg encodes negative amps as unsigned 64-bit (two's complement)
        "Amperage": 2**64 - 1500,
    }
]


def test_macos_charging() -> None:
    raw = plistlib.dumps(_MACOS_CHARGING)
    with patch("como.battery.subprocess.check_output", return_value=raw):
        bats = _get_batteries_macos()

    assert len(bats) == 1
    bat = bats[0]
    assert bat["serial"] == "ABC123"
    assert bat["maxcap"] == 5000
    assert bat["curcap"] == 4000
    assert bat["designcap"] == 5500
    assert bat["cycles"] == 42
    assert bat["voltage_mv"] == 12000
    assert bat["current_ma"] == 1500
    assert bat["is_charging"] is True
    assert bat["power_mw"] == abs(12000 * 1500) // 1000  # 18000


def test_macos_discharging_unsigned_conversion() -> None:
    raw = plistlib.dumps(_MACOS_DISCHARGING)
    with patch("como.battery.subprocess.check_output", return_value=raw):
        bats = _get_batteries_macos()

    assert bats[0]["current_ma"] == -1500
    assert bats[0]["is_charging"] is False


_MACOS_APPLE_SILICON = [
    {
        "BatterySerialNumber": "M5MAX01",
        # On Apple Silicon these are percentages, not mAh.
        "MaxCapacity": 100,
        "CurrentCapacity": 100,
        # Raw mAh lives under these keys.
        "AppleRawMaxCapacity": 6100,
        "AppleRawCurrentCapacity": 6100,
        "DesignCapacity": 6249,
        "CycleCount": 16,
        "Voltage": 13239,
        "Amperage": 0,
    }
]


def test_macos_apple_silicon_uses_raw_capacity() -> None:
    raw = plistlib.dumps(_MACOS_APPLE_SILICON)
    with patch("como.battery.subprocess.check_output", return_value=raw):
        bats = _get_batteries_macos()

    bat = bats[0]
    # Must use AppleRawMaxCapacity / AppleRawCurrentCapacity, not the percentage.
    assert bat["maxcap"] == 6100
    assert bat["curcap"] == 6100
    assert bat["designcap"] == 6249


def test_macos_no_battery_raises() -> None:
    raw = plistlib.dumps([])
    with (
        patch("como.battery.subprocess.check_output", return_value=raw),
        pytest.raises(RuntimeError, match="No battery found"),
    ):
        _get_batteries_macos()


# ---------------------------------------------------------------------------
# Linux
# ---------------------------------------------------------------------------


def _write_sysfs(tmp_path: Path, files: dict[str, int | str]) -> str:
    bat_dir = tmp_path / "BAT0"
    bat_dir.mkdir()
    for name, value in files.items():
        (bat_dir / name).write_text(f"{value}\n")
    return str(bat_dir)


def test_linux_charge_files_charging(tmp_path: Path) -> None:
    bat_dir = _write_sysfs(
        tmp_path,
        {
            "charge_full": 5_000_000,
            "charge_now": 4_000_000,
            "charge_full_design": 5_500_000,
            "cycle_count": 42,
            "voltage_now": 12_000_000,
            "current_now": 1_500_000,
            "status": "Charging",
            "serial_number": "LINUXBAT",
        },
    )
    with patch("glob.glob", return_value=[bat_dir]):
        bats = _get_batteries_linux()

    assert len(bats) == 1
    bat = bats[0]
    assert bat["serial"] == "LINUXBAT"
    assert bat["maxcap"] == 5_000_000
    assert bat["curcap"] == 4_000_000
    assert bat["designcap"] == 5_500_000
    assert bat["cycles"] == 42
    assert bat["voltage_mv"] == 12_000  # 12_000_000 µV ÷ 1000
    assert bat["current_ma"] == 1_500  # 1_500_000 µA ÷ 1000, positive (charging)
    assert bat["is_charging"] is True
    assert bat["power_mw"] is not None


def test_linux_discharging_negates_current(tmp_path: Path) -> None:
    bat_dir = _write_sysfs(
        tmp_path,
        {
            "charge_full": 5_000_000,
            "charge_now": 4_000_000,
            "current_now": 1_500_000,
            "status": "Discharging",
        },
    )
    with patch("glob.glob", return_value=[bat_dir]):
        bats = _get_batteries_linux()

    assert bats[0]["current_ma"] == -1_500
    assert bats[0]["is_charging"] is False


def test_linux_energy_files_fallback(tmp_path: Path) -> None:
    bat_dir = _write_sysfs(
        tmp_path,
        {
            "energy_full": 50_000_000,
            "energy_now": 40_000_000,
            "energy_full_design": 55_000_000,
            "status": "Full",
        },
    )
    with patch("glob.glob", return_value=[bat_dir]):
        bats = _get_batteries_linux()

    bat = bats[0]
    assert bat["maxcap"] == 50_000_000
    assert bat["curcap"] == 40_000_000
    assert bat["designcap"] == 55_000_000


def test_linux_no_battery_raises() -> None:
    with (
        patch("glob.glob", return_value=[]),
        pytest.raises(RuntimeError, match="No battery found"),
    ):
        _get_batteries_linux()


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------


def _mock_ps(data: dict) -> MagicMock:
    proc = MagicMock()
    proc.stdout = json.dumps(data)
    return proc


def test_windows_charging() -> None:
    payload = {
        "maxcap": 5000,
        "curcap": 4000,
        "designcap": 5500,
        "serial": "WINBAT123",
        "voltage": 12000,
        "power": 1500,
        "charging": True,
    }
    with patch("como.battery.subprocess.run", return_value=_mock_ps(payload)):
        bat = _get_battery_windows()

    assert bat["serial"] == "WINBAT123"
    assert bat["maxcap"] == 5000
    assert bat["curcap"] == 4000
    assert bat["designcap"] == 5500
    assert bat["voltage_mv"] == 12000
    assert bat["current_ma"] is None  # never available on Windows
    assert bat["cycles"] is None  # never available on Windows
    assert bat["power_mw"] == 1500
    assert bat["is_charging"] is True


def test_windows_discharging() -> None:
    payload = {
        "maxcap": 5000,
        "curcap": 4000,
        "voltage": 12000,
        "power": 1500,
        "charging": False,
    }
    with patch("como.battery.subprocess.run", return_value=_mock_ps(payload)):
        bat = _get_battery_windows()

    assert bat["current_ma"] is None
    assert bat["is_charging"] is False
    assert bat["power_mw"] == 1500


def test_windows_no_battery_raises() -> None:
    """Desktops return an empty object; that must be an error, not zeroed data."""
    with (
        patch("como.battery.subprocess.run", return_value=_mock_ps({})),
        pytest.raises(RuntimeError, match="No battery found"),
    ):
        _get_battery_windows()


def test_windows_empty_stdout_raises() -> None:
    proc = MagicMock()
    proc.stdout = ""
    with (
        patch("como.battery.subprocess.run", return_value=proc),
        pytest.raises(RuntimeError, match="No battery found"),
    ):
        _get_battery_windows()


def test_windows_missing_optional_fields() -> None:
    with patch(
        "como.battery.subprocess.run",
        return_value=_mock_ps({"maxcap": 5000, "curcap": 4000}),
    ):
        bat = _get_battery_windows()

    assert bat["designcap"] is None
    assert bat["voltage_mv"] is None
    assert bat["current_ma"] is None
    assert bat["power_mw"] is None
    assert bat["is_charging"] is None


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

_BAT_A: BatteryInfo = {
    "serial": "A",
    "maxcap": 3000,
    "curcap": 2500,
    "designcap": 3200,
    "cycles": 50,
    "voltage_mv": 12000,
    "current_ma": 500,
    "power_mw": 6000,
    "is_charging": True,
}

_BAT_B: BatteryInfo = {
    "serial": "B",
    "maxcap": 2000,
    "curcap": 1500,
    "designcap": 2200,
    "cycles": 60,
    "voltage_mv": 11000,
    "current_ma": 400,
    "power_mw": 4400,
    "is_charging": True,
}


def test_aggregate_sums_capacities() -> None:
    result = _aggregate([_BAT_A, _BAT_B])
    assert result["maxcap"] == 5000
    assert result["curcap"] == 4000
    assert result["designcap"] == 5400
    assert result["power_mw"] == 10400
    assert result["current_ma"] == 900


def test_aggregate_uses_max_cycles() -> None:
    result = _aggregate([_BAT_A, _BAT_B])
    assert result["cycles"] == 60


def test_aggregate_uses_first_serial_and_voltage() -> None:
    result = _aggregate([_BAT_A, _BAT_B])
    assert result["serial"] == "A"
    assert result["voltage_mv"] == 12000


def test_aggregate_none_cycles() -> None:
    a: BatteryInfo = {**_BAT_A, "cycles": None}
    b: BatteryInfo = {**_BAT_B, "cycles": None}
    assert _aggregate([a, b])["cycles"] is None


# ---------------------------------------------------------------------------
# Platform dispatch
# ---------------------------------------------------------------------------

_EMPTY_BATTERY: BatteryInfo = {
    "serial": "",
    "maxcap": 0,
    "curcap": 0,
    "designcap": None,
    "cycles": None,
    "voltage_mv": None,
    "current_ma": None,
    "power_mw": None,
    "is_charging": None,
}


@pytest.mark.parametrize(
    "platform,target,mock_return",
    [
        ("darwin", "como.battery._get_batteries_macos", [_EMPTY_BATTERY]),
        ("linux", "como.battery._get_batteries_linux", [_EMPTY_BATTERY]),
        ("win32", "como.battery._get_battery_windows", _EMPTY_BATTERY),
    ],
)
def test_dispatch(
    platform: str,
    target: str,
    mock_return: BatteryInfo | list[BatteryInfo],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    with patch(target, return_value=mock_return) as mock_fn:
        result = get_batteries()
    mock_fn.assert_called_once()
    assert result == [_EMPTY_BATTERY]


def test_get_battery_single() -> None:
    with patch("como.battery.get_batteries", return_value=[_EMPTY_BATTERY]):
        result = get_battery()
    assert result is _EMPTY_BATTERY


def test_get_battery_aggregates_multi() -> None:
    with patch("como.battery.get_batteries", return_value=[_BAT_A, _BAT_B]):
        result = get_battery()
    assert result["maxcap"] == 5000  # summed


def test_dispatch_unsupported_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "haiku")
    with pytest.raises(RuntimeError, match="Unsupported platform"):
        get_batteries()
