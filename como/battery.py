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
    current_ma: int | None  # milliamps, signed (negative = discharging)


def get_battery() -> BatteryInfo:
    if sys.platform == "darwin":
        return _get_battery_macos()
    elif sys.platform == "linux":
        return _get_battery_linux()
    elif sys.platform == "win32":
        return _get_battery_windows()
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def _get_battery_macos() -> BatteryInfo:
    import plistlib

    raw = subprocess.check_output(
        ["ioreg", "-r", "-c", "AppleSmartBattery", "-a"],
        stderr=subprocess.DEVNULL,
    )
    entries = plistlib.loads(raw)
    if not entries:
        raise RuntimeError("No battery found via ioreg")

    b = entries[0]

    amperage: int = b.get("Amperage", 0)
    # ioreg returns unsigned 64-bit; negative current is stored as a large number
    if amperage > 2**63:
        amperage -= 2**64

    return {
        "serial": b.get("BatterySerialNumber", ""),
        "maxcap": b["MaxCapacity"],
        "curcap": b["CurrentCapacity"],
        "designcap": b.get("DesignCapacity"),
        "cycles": b.get("CycleCount"),
        "voltage_mv": b.get("Voltage"),
        "current_ma": amperage,
    }


def _get_battery_linux() -> BatteryInfo:
    import glob

    battery_dirs = sorted(glob.glob("/sys/class/power_supply/BAT*"))
    if not battery_dirs:
        raise RuntimeError("No battery found at /sys/class/power_supply/")

    bat = Path(battery_dirs[0])

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

    # Convert µV → mV and µA → mA; negate current when discharging
    voltage_uv = read_int("voltage_now")
    current_ua = read_int("current_now")
    status = read_str("status").lower()

    voltage_mv = voltage_uv // 1000 if voltage_uv is not None else None
    current_ma: int | None = None
    if current_ua is not None:
        current_ma = current_ua // 1000
        if status == "discharging":
            current_ma = -current_ma

    return {
        "serial": read_str("serial_number"),
        "maxcap": maxcap,
        "curcap": curcap,
        "designcap": designcap,
        "cycles": read_int("cycle_count"),
        "voltage_mv": voltage_mv,
        "current_ma": current_ma,
    }


def _get_battery_windows() -> BatteryInfo:
    # Query battery info via PowerShell CIM; no third-party packages needed.
    # Cycle count is not exposed by standard Windows APIs and will be None.
    script = (
        "$r = @{};"
        "try { $cn = 'BatteryFullChargedCapacity';"
        " $r.maxcap = (Get-CimInstance -Ns ROOT\\WMI -Class $cn)[0].FullChargedCapacity"
        " } catch {};"
        "try {"
        "  $s = (Get-CimInstance -Ns ROOT\\WMI -Class BatteryStatus)[0];"
        "  $r.curcap = $s.RemainingCapacity;"
        "  $r.voltage = $s.Voltage;"
        "  if ($s.Charging) { $r.current = [int]$s.ChargeRate }"
        "  elseif ($s.Discharging) { $r.current = -[int]$s.DischargeRate }"
        "  else { $r.current = 0 }"
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

    data: dict = json.loads(proc.stdout)

    # Windows ChargeRate/DischargeRate are in mW, not mA — we store as-is in
    # current_ma with a note that on Windows the unit is actually mW.
    return {
        "serial": str(data.get("serial", "")),
        "maxcap": int(data.get("maxcap", 0)),
        "curcap": int(data.get("curcap", 0)),
        "designcap": int(data["designcap"]) if "designcap" in data else None,
        "cycles": None,
        "voltage_mv": int(data["voltage"]) if "voltage" in data else None,
        "current_ma": int(data["current"]) if "current" in data else None,
    }
