"""
como.core - database operations and scheduling
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import zlib
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rich.console import Console

from como.battery import get_batteries, get_battery
from como.settings import COMO_BATTERY_FILE

if sys.platform == "linux":
    from crontab import CronTab

console = Console()

_SPARKS = "▁▂▃▄▅▆▇█"
_SQLITE_MAGIC = b"SQLite format 3\x00"


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


def _is_sqlite(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(16) == _SQLITE_MAGIC
    except OSError:
        return False


def _open_db(path: Path) -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battery (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            time        TEXT    NOT NULL UNIQUE,
            capacity    INTEGER NOT NULL,
            cycles      INTEGER,
            voltage_mv  INTEGER,
            power_mw    INTEGER,
            is_charging INTEGER
        )
    """)
    conn.commit()
    return conn


def _legacy_path() -> Path:
    """Pre-0.8 installs stored the database without the .db suffix."""
    return COMO_BATTERY_FILE.with_suffix("")


def _db_exists() -> bool:
    """True if either the current or a pre-0.8 legacy database is present."""
    return COMO_BATTERY_FILE.exists() or _legacy_path().exists()


def _migrate_legacy(src: Path, dest: Path) -> None:
    """Convert a zlib-compressed JSON (tablib) database to SQLite at dest."""
    try:
        blob = json.loads(zlib.decompress(src.read_bytes()))
        headers: list[str] = blob["headers"]
        rows: list[list] = blob["data"]
    except Exception as exc:
        raise ComoError(f"Cannot read existing database: {exc}") from exc

    backup = src.with_suffix(".bak")
    src.rename(backup)
    console.print(f"[dim]Migrating database to SQLite (backup: {backup.name})[/dim]")

    conn = _open_db(dest)
    try:
        for row in rows:
            rec = dict(zip(headers, row, strict=False))
            cycles_raw = rec.get("cycles")
            cycles = None if cycles_raw in (None, "None") else int(cycles_raw)
            conn.execute(
                "INSERT OR IGNORE INTO battery (time, capacity, cycles)"
                " VALUES (?, ?, ?)",
                (rec["time"], int(rec["capacity"]), cycles),
            )
        conn.commit()
    finally:
        conn.close()


def _get_db() -> sqlite3.Connection:
    """Return an open connection, migrating legacy format/location if needed."""
    path = COMO_BATTERY_FILE
    if path.exists():
        if path.stat().st_size == 0:
            path.unlink()
        elif not _is_sqlite(path):
            _migrate_legacy(path, path)
    else:
        legacy = _legacy_path()
        if legacy.exists() and legacy.stat().st_size > 0:
            _migrate_legacy(legacy, path)
    return _open_db(path)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_save() -> None:
    bat = get_battery()
    time_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    conn = _get_db()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO battery"
            " (time, capacity, cycles, voltage_mv, power_mw, is_charging)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                time_str,
                bat["maxcap"],
                bat["cycles"],
                bat["voltage_mv"],
                bat["power_mw"],
                int(bat["is_charging"]) if bat["is_charging"] is not None else None,
            ),
        )
        conn.commit()
        stored = cur.rowcount > 0
    finally:
        conn.close()

    if stored:
        console.print(f"  battery info saved ([dim]{time_str}[/dim])")
    else:
        # time is UNIQUE, so a second save inside the same second is a no-op.
        console.print(f"  [yellow]already saved[/yellow] ([dim]{time_str}[/dim])")


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

        # Truthiness, not "is not None": flaky hardware can report 0 here.
        if bat["designcap"]:
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


def cmd_data(since: str | None = None) -> None:
    if not _db_exists():
        raise ComoError("No como database.")

    cutoff_str: str | None = None
    if since is not None:
        cutoff = _parse_since(since)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S")

    conn = _get_db()
    try:
        if cutoff_str:
            rows = conn.execute(
                "SELECT time, capacity, cycles FROM battery"
                " WHERE time >= ? ORDER BY time",
                (cutoff_str,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT time, capacity, cycles FROM battery ORDER BY time"
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        if since is not None:
            raise ComoError(f"No entries in the database within the last {since}.")
        raise ComoError("No data in database.")

    console.print("\n[bold cyan]Como Database[/bold cyan]")
    console.print(f"  Entries:    {len(rows)}")
    console.print(f"  First save: {rows[0]['time']}")
    console.print(f"  Last save:  {rows[-1]['time']}")

    first = datetime.strptime(str(rows[0]["time"]), "%Y-%m-%dT%H:%M:%S")
    delta = datetime.now(timezone.utc).replace(tzinfo=None) - first
    console.print(f"  Age:        {delta.days} days")

    capacities = [int(row["capacity"]) for row in rows]
    console.print(f"\n  [yellow]Capacity[/yellow]  {sparkline(capacities)}")

    cycle_vals = [int(row["cycles"]) for row in rows if row["cycles"] is not None]
    if cycle_vals:
        console.print(f"  [yellow]Cycles[/yellow]    {sparkline(cycle_vals)}")


def cmd_reset() -> None:
    if not _db_exists():
        console.print("[yellow]No como database.[/yellow]")
        return
    confirm = input("Are you sure? This will remove everything! [y/n] ")
    if confirm == "y":
        COMO_BATTERY_FILE.unlink(missing_ok=True)
        _legacy_path().unlink(missing_ok=True)
        console.print("  [green]Database removed.[/green]")


def _opt_int(raw: str | None) -> int | None:
    """Parse a CSV cell that may legitimately be blank/absent."""
    if raw is None or raw.strip() in ("", "-", "None"):
        return None
    return int(raw)


def cmd_import(file: str) -> None:
    src = Path(file).expanduser()
    if not src.exists():
        raise ComoError(f"Cannot open file: {file}")

    conn = _get_db()
    inserted = skipped = 0
    try:
        with src.open(newline="") as fh:
            for raw in csv.DictReader(fh):
                try:
                    if "date" in raw:
                        time_str = raw["date"] + "T00:00:00"
                        raw_cycles = raw.get("loadcycles", "-")
                    else:
                        time_str = raw["time"]
                        raw_cycles = raw.get("cycles", "None")
                    capacity = int(raw["capacity"])
                    cycles = _opt_int(raw_cycles)
                except (KeyError, ValueError) as exc:
                    raise ComoError(f"Invalid CSV row: {exc}") from exc
                # Present in files written by `como export`; absent in legacy CSVs.
                cur = conn.execute(
                    "INSERT OR IGNORE INTO battery"
                    " (time, capacity, cycles, voltage_mv, power_mw, is_charging)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        time_str,
                        capacity,
                        cycles,
                        _opt_int(raw.get("voltage_mv")),
                        _opt_int(raw.get("power_mw")),
                        _opt_int(raw.get("is_charging")),
                    ),
                )
                if cur.rowcount:
                    inserted += 1
                else:
                    skipped += 1
        conn.commit()
    finally:
        conn.close()

    msg = f"{inserted} battery records imported"
    if skipped:
        msg += f", {skipped} already present"
    console.print(f"  [green]{msg}.[/green]")


def cmd_export() -> None:
    if not _db_exists():
        raise ComoError("No como database.")

    dest = Path("como.csv")
    if dest.exists():
        confirm = input("Replace existing como.csv? [y/n] ")
        if confirm != "y":
            return

    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT time, capacity, cycles, voltage_mv, power_mw, is_charging"
            " FROM battery ORDER BY time"
        ).fetchall()
    finally:
        conn.close()

    with dest.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["time", "capacity", "cycles", "voltage_mv", "power_mw", "is_charging"]
        )
        for row in rows:
            writer.writerow(list(row))

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
        # ~/Library/LaunchAgents does not exist on a fresh account.
        plist_path.parent.mkdir(parents=True, exist_ok=True)
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
