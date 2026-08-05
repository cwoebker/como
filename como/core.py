"""
como.core - database operations and scheduling
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zlib
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

import tablib
from rich.console import Console
from tablib import Dataset

from como.battery import get_batteries, get_battery
from como.settings import COMO_BATTERY_FILE

if sys.platform == "linux":
    from crontab import CronTab

console = Console()

_SPARKS = "▁▂▃▄▅▆▇█"


class ComoError(Exception):
    """User-facing error that should exit with a non-zero status."""


def sparkline(values: Sequence[int | float]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    return "".join(_SPARKS[int((v - lo) / span * 7)] for v in values)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _ensure_dir() -> None:
    COMO_BATTERY_FILE.parent.mkdir(parents=True, exist_ok=True)


def create_database() -> Dataset:
    _ensure_dir()
    console.print("[yellow]Creating new database[/yellow]")
    COMO_BATTERY_FILE.write_bytes(b"")
    return Dataset(headers=["time", "capacity", "cycles"])


def read_database() -> Dataset:
    json_str = zlib.decompress(COMO_BATTERY_FILE.read_bytes()).decode()
    return tablib.import_set(json_str, format="json")


def write_database(data: Dataset) -> None:
    _ensure_dir()
    json_str: str = data.export("json")
    COMO_BATTERY_FILE.write_bytes(zlib.compress(json_str.encode()))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_save() -> None:
    bat = get_battery()

    data = create_database() if not COMO_BATTERY_FILE.exists() else read_database()

    data.append(
        [
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            bat["maxcap"],
            bat["cycles"],
        ]
    )

    write_database(data)
    console.print(f"  battery info saved ([dim]{data['time'][-1]}[/dim])")


def cmd_info() -> None:
    batteries = get_batteries()
    multi = len(batteries) > 1

    header = f"Battery Info ({len(batteries)} batteries)" if multi else "Battery Info"
    console.print(f"\n[bold cyan]{header}[/bold cyan]")

    for i, bat in enumerate(batteries):
        if multi:
            console.print(f"\n  [bold]Battery {i}[/bold]")
        pad = "    " if multi else "  "

        console.print(f"{pad}Serial:           {bat['serial'] or 'N/A'}")
        console.print(f"{pad}Max Capacity:     {bat['maxcap']}")
        console.print(f"{pad}Current Capacity: {bat['curcap']}")

        if bat["designcap"] is not None:
            health = bat["maxcap"] / bat["designcap"] * 100
            console.print(
                f"{pad}Design Capacity:  {bat['designcap']}"
                f"  ([green]{health:.1f}% health[/green])"
            )

        if bat["cycles"] is not None:
            console.print(f"{pad}Cycle Count:      {bat['cycles']}")
        else:
            console.print(f"{pad}Cycle Count:      N/A")

        if bat["voltage_mv"] is not None:
            console.print(f"{pad}Voltage:          {bat['voltage_mv']} mV")

        if bat["power_mw"] is not None and bat["is_charging"] is not None:
            direction = "charging" if bat["is_charging"] else "discharging"
            console.print(
                f"{pad}Power:            {bat['power_mw'] / 1000:.2f} W ({direction})"
            )

    if sys.platform == "darwin":
        model = (
            subprocess.check_output(
                ["sysctl", "-n", "hw.model"], stderr=subprocess.DEVNULL
            )
            .rstrip(b"\n")
            .decode()
        )
        console.print(f"  Model:            {model}")


def _parse_since(s: str) -> datetime:
    m = re.fullmatch(r"(\d+)([dwmy])", s)
    if not m:
        raise ComoError(f"Invalid --since value {s!r}. Use e.g. 30d, 4w, 6m, 1y.")
    n, unit = int(m.group(1)), m.group(2)
    days = {"d": n, "w": n * 7, "m": n * 30, "y": n * 365}[unit]
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)


def _filter_since(data: Dataset, cutoff: datetime) -> Dataset:
    filtered = Dataset(headers=["time", "capacity", "cycles"])
    for row in data:
        ts = datetime.strptime(str(row[0]), "%Y-%m-%dT%H:%M:%S")
        if ts >= cutoff:
            filtered.append(list(row))
    return filtered


def cmd_data(since: str | None = None) -> None:
    if not COMO_BATTERY_FILE.exists():
        raise ComoError("No como database.")

    data = read_database()

    if since is not None:
        cutoff = _parse_since(since)
        data = _filter_since(data, cutoff)
        if len(data) == 0:
            raise ComoError(f"No entries in the database within the last {since}.")

    console.print("\n[bold cyan]Como Database[/bold cyan]")
    console.print(f"  Entries:    {len(data)}")
    console.print(f"  First save: {data['time'][0]}")
    console.print(f"  Last save:  {data['time'][-1]}")

    first = datetime.strptime(data["time"][0], "%Y-%m-%dT%H:%M:%S")
    delta = datetime.now(timezone.utc).replace(tzinfo=None) - first
    console.print(f"  Age:        {delta.days} days")

    capacities = [int(v) for v in data["capacity"]]
    console.print(f"\n  [yellow]Capacity[/yellow]  {sparkline(capacities)}")

    cycle_vals: list[int] = [int(v) for v in data["cycles"] if v is not None]
    if cycle_vals:
        console.print(f"  [yellow]Cycles[/yellow]    {sparkline(cycle_vals)}")


def cmd_reset() -> None:
    if not COMO_BATTERY_FILE.exists():
        console.print("[yellow]No como database.[/yellow]")
        return
    confirm = input("Are you sure? This will remove everything! [y/n] ")
    if confirm == "y":
        COMO_BATTERY_FILE.unlink()
        console.print("  [green]Database removed.[/green]")


def _import_row(row: dict) -> dict:
    try:
        row["date"] += "T00:00:00"
        row["loadcycles"] = None if row["loadcycles"] == "-" else int(row["loadcycles"])
    except KeyError:
        row["cycles"] = None if row["cycles"] == "None" else int(row["cycles"])
    row["capacity"] = int(row["capacity"])
    return row


def cmd_import(file: str) -> None:
    src = Path(file).expanduser()
    if not src.exists():
        raise ComoError(f"Cannot open file: {file}")

    current = create_database() if not COMO_BATTERY_FILE.exists() else read_database()

    imported: Dataset = tablib.import_set(src.read_text(), format="csv")
    imported.dict = [_import_row(row) for row in imported.dict]  # type: ignore[assignment]

    merged = current.stack(imported).sort("time")
    write_database(merged)
    console.print("  [green]Battery statistics imported.[/green]")


def cmd_export() -> None:
    if not COMO_BATTERY_FILE.exists():
        raise ComoError("No como database.")

    dest = Path("como.csv")
    if dest.exists():
        confirm = input("Replace existing como.csv? [y/n] ")
        if confirm != "y":
            return

    data = read_database()
    csv_str: str = data.export("csv")
    dest.write_text(csv_str)
    console.print("  [green]Saved como.csv to current directory.[/green]")


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

_PLIST_SAVE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cwoebker.como</string>
    <key>OnDemand</key>
    <true/>
    <key>RunAtLoad</key>
    <false/>
    <key>Program</key>
    <string>{como_path}</string>
    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>20</integer><key>Minute</key><integer>0</integer></dict>
    </array>
</dict>
</plist>"""


def cmd_automate() -> None:
    if sys.platform == "darwin":
        _automate_macos()
    elif sys.platform == "linux":
        _automate_linux()
    else:
        console.print(
            "[yellow]Automatic scheduling is not supported on this platform.[/yellow]"
        )


def _automate_macos() -> None:
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.cwoebker.como.plist"
    if plist_path.exists():
        subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
        plist_path.unlink()
        console.print("  como will only run manually")
    else:
        como_path = shutil.which("como")
        if not como_path:
            console.print("[red]como not found in PATH — install it first.[/red]")
            return
        plist_path.write_text(_PLIST_SAVE.format(como_path=como_path))
        subprocess.run(["launchctl", "load", str(plist_path)], check=False)
        console.print("  como will run automatically (8am, 2pm, 8pm)")


def _automate_linux() -> None:
    user_cron = CronTab(user=True)
    existing = list(user_cron.find_command("como"))
    if existing:
        user_cron.remove_all(command="como")
        user_cron.write()
        console.print("  como will only run manually")
    else:
        como_path = shutil.which("como") or "como"
        for hour in (8, 14, 20):
            job = user_cron.new(command=como_path)
            job.hour.on(hour)
            job.minute.on(0)
        user_cron.write()
        console.print("  como will run automatically (8am, 2pm, 8pm)")
