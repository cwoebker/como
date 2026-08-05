"""
como.battery - OS-specific battery data collection
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypedDict


class BatteryInfo(TypedDict):
    serial: str
    maxcap: int
    curcap: int
    designcap: int | None
    cycles: int | None
    voltage_mv: int | None  # millivolts
    current_ma: int | None  # milliamps, signed (negative = discharging); None on Win
    power_mw: int | None  # milliwatts, normalized across all platforms
    is_charging: bool | None


def get_batteries() -> list[BatteryInfo]:
    """Return info for each physical battery (one entry per battery pack)."""
    if sys.platform == "darwin":
        return _get_batteries_macos()
    elif sys.platform == "linux":
        return _get_batteries_linux()
    elif sys.platform == "win32":
        return [_get_battery_windows()]
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_battery() -> BatteryInfo:
    """Return aggregated battery info across all battery packs (used for saving)."""
    batteries = get_batteries()
    return batteries[0] if len(batteries) == 1 else _aggregate(batteries)


def _aggregate(batteries: list[BatteryInfo]) -> BatteryInfo:
    def sum_opt(vals: list[int | None]) -> int | None:
        present = [v for v in vals if v is not None]
        return sum(present) if present else None

    return {
        "serial": batteries[0]["serial"],
        "maxcap": sum(b["maxcap"] for b in batteries),
        "curcap": sum(b["curcap"] for b in batteries),
        "designcap": sum_opt([b["designcap"] for b in batteries]),
        "cycles": max(
            (b["cycles"] for b in batteries if b["cycles"] is not None), default=None
        ),
        "voltage_mv": batteries[0]["voltage_mv"],
        "current_ma": sum_opt([b["current_ma"] for b in batteries]),
        "power_mw": sum_opt([b["power_mw"] for b in batteries]),
        "is_charging": batteries[0]["is_charging"],
    }


# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------


def _get_batteries_macos() -> list[BatteryInfo]:
    import plistlib

    raw = subprocess.check_output(
        ["ioreg", "-r", "-c", "AppleSmartBattery", "-a"],
        stderr=subprocess.DEVNULL,
    )
    entries = plistlib.loads(raw)
    if not entries:
        raise RuntimeError("No battery found via ioreg")
    return [_parse_macos_battery(b) for b in entries]


def _parse_macos_battery(b: dict) -> BatteryInfo:
    amperage: int = b.get("Amperage", 0)
    # ioreg stores negative current as unsigned 64-bit (two's complement)
    if amperage > 2**63:
        amperage -= 2**64

    voltage_mv: int | None = b.get("Voltage")
    is_charging = amperage > 0
    power_mw = abs(voltage_mv * amperage) // 1000 if voltage_mv is not None else None

    # On Apple Silicon, MaxCapacity/CurrentCapacity are percentages (0-100);
    # raw mAh lives in AppleRawMaxCapacity/AppleRawCurrentCapacity. On Intel,
    # only the legacy keys exist and already hold raw mAh.
    maxcap = b.get("AppleRawMaxCapacity", b["MaxCapacity"])
    curcap = b.get("AppleRawCurrentCapacity", b["CurrentCapacity"])

    return {
        "serial": b.get("BatterySerialNumber", ""),
        "maxcap": maxcap,
        "curcap": curcap,
        "designcap": b.get("DesignCapacity"),
        "cycles": b.get("CycleCount"),
        "voltage_mv": voltage_mv,
        "current_ma": amperage,
        "power_mw": power_mw,
        "is_charging": is_charging,
    }


# ---------------------------------------------------------------------------
# Linux
# ---------------------------------------------------------------------------


def _get_batteries_linux() -> list[BatteryInfo]:
    import glob

    battery_dirs = sorted(glob.glob("/sys/class/power_supply/BAT*"))
    if not battery_dirs:
        raise RuntimeError("No battery found at /sys/class/power_supply/")
    return [_read_linux_battery(Path(d)) for d in battery_dirs]


def _read_linux_battery(bat: Path) -> BatteryInfo:
    def read_int(name: str) -> int | None:
        p = bat / name
        try:
            return int(p.read_text().strip())
        except (FileNotFoundError, ValueError):
            return None

    def read_str(name: str) -> str:
        p = bat / name
        try:
            return p.read_text().strip()
        except FileNotFoundError:
            return ""

    # Drivers expose either charge_* (µAh) or energy_* (µWh) depending on hardware
    maxcap = read_int("charge_full") or read_int("energy_full")
    curcap = read_int("charge_now") or read_int("energy_now")
    designcap = read_int("charge_full_design") or read_int("energy_full_design")

    if maxcap is None or curcap is None:
        raise RuntimeError(f"Could not read battery capacity from {bat}")

    status = read_str("status").lower()
    is_charging = status == "charging"

    voltage_uv = read_int("voltage_now")
    current_ua = read_int("current_now")

    voltage_mv = voltage_uv // 1000 if voltage_uv is not None else None
    current_ma: int | None = None
    if current_ua is not None:
        current_ma = current_ua // 1000
        if status == "discharging":
            current_ma = -current_ma

    power_mw: int | None = None
    if voltage_mv is not None and current_ma is not None:
        power_mw = abs(voltage_mv * current_ma) // 1000

    return {
        "serial": read_str("serial_number"),
        "maxcap": maxcap,
        "curcap": curcap,
        "designcap": designcap,
        "cycles": read_int("cycle_count"),
        "voltage_mv": voltage_mv,
        "current_ma": current_ma,
        "power_mw": power_mw,
        "is_charging": is_charging,
    }


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------


def _get_battery_windows() -> BatteryInfo:
    # Query battery info via PowerShell CIM; no third-party packages needed.
    # Cycle count is not exposed by standard Windows APIs and will be None.
    # ChargeRate/DischargeRate are in mW, so current_ma is left as None.
    script = (
        "$r = @{};"
        "try { $cn = 'BatteryFullChargedCapacity';"
        " $r.maxcap = (Get-CimInstance -Ns ROOT\\WMI -Class $cn)[0].FullChargedCapacity"
        " } catch {};"
        "try {"
        "  $s = (Get-CimInstance -Ns ROOT\\WMI -Class BatteryStatus)[0];"
        "  $r.curcap = $s.RemainingCapacity;"
        "  $r.voltage = $s.Voltage;"
        "  if ($s.Charging) { $r.power = $s.ChargeRate; $r.charging = $true }"
        "  elseif ($s.Discharging)"
        " { $r.power = $s.DischargeRate; $r.charging = $false }"
        "  else { $r.power = 0; $r.charging = $false }"
        "} catch {};"
        "try {"
        "  $d = (Get-CimInstance -Ns ROOT\\WMI -Class BatteryStaticData)[0];"
        "  $r.designcap = $d.DesignedCapacity;"
        "  $r.serial = $d.UniqueID"
        "} catch {};"
        "$r | ConvertTo-Json -Compress"
    )

    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        check=True,
    )

    stdout = proc.stdout.strip()
    data: dict = json.loads(stdout) if stdout else {}
    # Every CIM query is wrapped in try/catch, so a machine with no battery
    # yields an empty object rather than an error.
    if not data:
        raise RuntimeError("No battery found via WMI")

    is_charging: bool | None = bool(data["charging"]) if "charging" in data else None
    power_mw: int | None = abs(int(data["power"])) if "power" in data else None

    return {
        "serial": str(data.get("serial", "")),
        "maxcap": int(data.get("maxcap", 0)),
        "curcap": int(data.get("curcap", 0)),
        "designcap": int(data["designcap"]) if "designcap" in data else None,
        "cycles": None,
        "voltage_mv": int(data["voltage"]) if "voltage" in data else None,
        "current_ma": None,
        "power_mw": power_mw,
        "is_charging": is_charging,
    }
