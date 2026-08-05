"""Tests for como.core — sparkline, database I/O, commands."""

from __future__ import annotations

import json
import sqlite3
import zlib
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

import como.core
from como.battery import BatteryInfo
from como.core import (
    ComoError,
    _get_db,
    _migrate_legacy,
    _open_db,
    _parse_since,
    cmd_data,
    cmd_export,
    cmd_import,
    cmd_info,
    cmd_reset,
    cmd_save,
    sparkline,
)

_SAMPLE_BATTERY: BatteryInfo = {
    "serial": "TEST123",
    "maxcap": 5000,
    "curcap": 4000,
    "designcap": 5500,
    "cycles": 42,
    "voltage_mv": 12000,
    "current_ma": 1500,
    "power_mw": 18000,
    "is_charging": True,
}


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the database file into a temp directory."""
    path = tmp_path / "como.db"
    monkeypatch.setattr(como.core, "COMO_BATTERY_FILE", path)
    return path


@pytest.fixture
def captured_console(monkeypatch: pytest.MonkeyPatch) -> StringIO:
    """Replace the module-level Console with one that writes to a StringIO."""
    sio = StringIO()
    monkeypatch.setattr(como.core, "console", Console(file=sio, force_terminal=False))
    return sio


def _ago(days: int) -> str:
    """Timestamp `days` in the past, so --since tests never go stale."""
    ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _seed(db_path: Path, rows: Sequence[tuple[str, int, int | None]]) -> None:
    """Insert (time, capacity, cycles) rows directly into the test database."""
    conn = _open_db(db_path)
    try:
        for row in rows:
            conn.execute(
                "INSERT INTO battery (time, capacity, cycles) VALUES (?, ?, ?)", row
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# sparkline
# ---------------------------------------------------------------------------


def test_sparkline_empty() -> None:
    assert sparkline([]) == ""


def test_sparkline_all_same() -> None:
    result = sparkline([5, 5, 5])
    assert len(result) == 3
    assert all(c == result[0] for c in result)


def test_sparkline_ascending() -> None:
    assert sparkline([1, 2, 3, 4, 5, 6, 7, 8]) == "▁▂▃▄▅▆▇█"


def test_sparkline_length() -> None:
    assert len(sparkline([10, 20, 30, 40, 50])) == 5


def test_sparkline_single_value() -> None:
    assert len(sparkline([42])) == 1


# ---------------------------------------------------------------------------
# Database roundtrip (SQLite)
# ---------------------------------------------------------------------------


def test_open_db_creates_schema(db_path: Path) -> None:
    conn = _open_db(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(battery)").fetchall()}
    conn.close()
    expected = {"time", "capacity", "cycles", "voltage_mv", "power_mw", "is_charging"}
    assert expected <= cols


def test_open_db_idempotent(db_path: Path) -> None:
    _open_db(db_path).close()
    conn = _open_db(db_path)  # should not raise
    conn.close()


# ---------------------------------------------------------------------------
# Legacy migration
# ---------------------------------------------------------------------------


def _make_legacy_db(path: Path, rows: list[tuple]) -> None:
    blob = {
        "headers": ["time", "capacity", "cycles"],
        "data": list(rows),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(zlib.compress(json.dumps(blob).encode()))


def test_migrate_legacy_converts_data(
    db_path: Path, captured_console: StringIO
) -> None:
    _make_legacy_db(
        db_path,
        [("2024-01-01T08:00:00", 5000, 42), ("2024-01-02T08:00:00", 4900, 43)],
    )

    conn = _get_db()
    rows = conn.execute(
        "SELECT time, capacity, cycles FROM battery ORDER BY time"
    ).fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0]["time"] == "2024-01-01T08:00:00"
    assert rows[0]["capacity"] == 5000
    assert rows[0]["cycles"] == 42
    assert db_path.with_suffix(".bak").exists()


def test_migrate_legacy_null_cycles(db_path: Path, captured_console: StringIO) -> None:
    _make_legacy_db(db_path, [("2024-01-01T08:00:00", 5000, None)])

    conn = _get_db()
    row = conn.execute("SELECT cycles FROM battery").fetchone()
    conn.close()
    assert row["cycles"] is None


def test_migrate_legacy_bad_file_raises(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not valid zlib or json")
    with pytest.raises(ComoError, match="Cannot read existing database"):
        _migrate_legacy(db_path, db_path)


def test_migrate_from_legacy_unsuffixed_path(
    db_path: Path, captured_console: StringIO
) -> None:
    """Pre-0.8 installs stored the db as 'como', not 'como.db'."""
    legacy = db_path.with_suffix("")
    _make_legacy_db(legacy, [("2024-01-01T08:00:00", 5000, 42)])
    assert not db_path.exists()

    conn = _get_db()
    rows = conn.execute("SELECT time, capacity, cycles FROM battery").fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0]["capacity"] == 5000
    assert db_path.exists()  # migrated into the new .db location
    assert not legacy.exists()  # original moved aside
    assert legacy.with_suffix(".bak").exists()


def test_cmd_data_finds_legacy_database(
    db_path: Path, captured_console: StringIO
) -> None:
    """cmd_data must not report 'No como database' for a pre-0.8 install."""
    _make_legacy_db(db_path.with_suffix(""), [("2024-01-01T08:00:00", 5000, 42)])
    cmd_data()
    assert "Entries" in captured_console.getvalue()


# ---------------------------------------------------------------------------
# cmd_save
# ---------------------------------------------------------------------------


def test_cmd_save_creates_db(db_path: Path, captured_console: StringIO) -> None:
    with patch("como.core.get_battery", return_value=_SAMPLE_BATTERY):
        cmd_save()

    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT capacity, cycles, voltage_mv, power_mw, is_charging FROM battery"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == 5000
    assert rows[0][1] == 42
    assert rows[0][2] == 12000
    assert rows[0][3] == 18000
    assert rows[0][4] == 1  # True stored as 1


def test_cmd_save_duplicate_reports_honestly(
    db_path: Path, captured_console: StringIO
) -> None:
    """time is UNIQUE — a same-second save is a no-op and must not claim success."""
    with patch("como.core.get_battery", return_value=_SAMPLE_BATTERY):
        cmd_save()
        cmd_save()

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM battery").fetchone()[0]
    conn.close()

    out = captured_console.getvalue()
    assert count == 1
    assert out.count("battery info saved") == 1
    assert "already saved" in out


def test_cmd_save_appends(db_path: Path, captured_console: StringIO) -> None:
    _seed(db_path, [("2024-01-01T08:00:00", 5000, 42)])
    with patch("como.core.get_battery", return_value=_SAMPLE_BATTERY):
        cmd_save()

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM battery").fetchone()[0]
    conn.close()
    assert count == 2


# ---------------------------------------------------------------------------
# cmd_data
# ---------------------------------------------------------------------------


def test_cmd_data_no_db(db_path: Path) -> None:
    with pytest.raises(ComoError, match="No como database"):
        cmd_data()


def test_cmd_data_empty_db(db_path: Path) -> None:
    _open_db(db_path).close()  # create schema but leave empty
    with pytest.raises(ComoError, match="No data in database"):
        cmd_data()


def test_cmd_data_shows_entries_and_sparkline(
    db_path: Path, captured_console: StringIO
) -> None:
    rows = [(f"2024-01-0{i + 1}T08:00:00", 5000 - i * 50, 40 + i) for i in range(5)]
    _seed(db_path, rows)
    cmd_data()
    out = captured_console.getvalue()
    assert "5" in out
    assert any(c in out for c in "▁▂▃▄▅▆▇█")


# ---------------------------------------------------------------------------
# cmd_reset
# ---------------------------------------------------------------------------


def test_cmd_reset_confirmed(db_path: Path, captured_console: StringIO) -> None:
    _open_db(db_path).close()
    with patch("builtins.input", return_value="y"):
        cmd_reset()
    assert not db_path.exists()


def test_cmd_reset_cancelled(db_path: Path, captured_console: StringIO) -> None:
    _open_db(db_path).close()
    with patch("builtins.input", return_value="n"):
        cmd_reset()
    assert db_path.exists()


def test_cmd_reset_no_db(db_path: Path, captured_console: StringIO) -> None:
    cmd_reset()
    assert "No como database" in captured_console.getvalue()


# ---------------------------------------------------------------------------
# cmd_export
# ---------------------------------------------------------------------------


def test_cmd_export_no_db(db_path: Path) -> None:
    with pytest.raises(ComoError, match="No como database"):
        cmd_export()


def test_cmd_export_writes_csv(
    db_path: Path,
    captured_console: StringIO,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed(db_path, [("2024-01-01T08:00:00", 5000, 42)])
    monkeypatch.chdir(tmp_path)
    cmd_export()

    csv_file = tmp_path / "como.csv"
    assert csv_file.exists()
    text = csv_file.read_text()
    assert "capacity" in text
    assert "5000" in text


def test_export_import_round_trip_preserves_columns(
    db_path: Path,
    captured_console: StringIO,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`como export` then `como import` must not silently drop the new columns."""
    conn = _open_db(db_path)
    conn.execute(
        "INSERT INTO battery"
        " (time, capacity, cycles, voltage_mv, power_mw, is_charging)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("2024-01-01T08:00:00", 5000, 42, 12000, 18000, 1),
    )
    conn.commit()
    conn.close()

    monkeypatch.chdir(tmp_path)
    cmd_export()

    # Re-import into a clean database.
    fresh = tmp_path / "fresh.db"
    monkeypatch.setattr(como.core, "COMO_BATTERY_FILE", fresh)
    cmd_import(str(tmp_path / "como.csv"))

    conn = _open_db(fresh)
    row = conn.execute(
        "SELECT voltage_mv, power_mw, is_charging FROM battery"
    ).fetchone()
    conn.close()

    assert row["voltage_mv"] == 12000
    assert row["power_mw"] == 18000
    assert row["is_charging"] == 1


def test_cmd_import_reports_duplicates(
    db_path: Path, captured_console: StringIO, tmp_path: Path
) -> None:
    csv_file = tmp_path / "dup.csv"
    csv_file.write_text("time,capacity,cycles\n2024-01-01T08:00:00,5000,42\n")

    cmd_import(str(csv_file))
    captured_console.truncate(0)
    captured_console.seek(0)
    cmd_import(str(csv_file))  # same row again

    out = captured_console.getvalue()
    assert "0 battery records imported" in out
    assert "1 already present" in out


def test_cmd_export_includes_extended_columns(
    db_path: Path,
    captured_console: StringIO,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = _open_db(db_path)
    conn.execute(
        "INSERT INTO battery"
        " (time, capacity, cycles, voltage_mv, power_mw, is_charging)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("2024-01-01T08:00:00", 5000, 42, 12000, 18000, 1),
    )
    conn.commit()
    conn.close()

    monkeypatch.chdir(tmp_path)
    cmd_export()

    text = (tmp_path / "como.csv").read_text()
    assert "voltage_mv" in text
    assert "power_mw" in text
    assert "12000" in text


# ---------------------------------------------------------------------------
# cmd_info
# ---------------------------------------------------------------------------


def test_cmd_info_zero_designcap_does_not_crash(captured_console: StringIO) -> None:
    """Flaky hardware can report designcap 0; health must not divide by it."""
    bat: BatteryInfo = {**_SAMPLE_BATTERY, "designcap": 0}
    with patch("como.core.get_batteries", return_value=[bat]):
        cmd_info()
    assert "health" not in captured_console.getvalue()


def test_cmd_info_single_battery(captured_console: StringIO) -> None:
    with patch("como.core.get_batteries", return_value=[_SAMPLE_BATTERY]):
        cmd_info()
    out = captured_console.getvalue()
    assert "5000" in out
    assert "charging" in out.lower()


# ---------------------------------------------------------------------------
# _parse_since
# ---------------------------------------------------------------------------


def test_parse_since_days() -> None:
    result = _parse_since("30d")
    expected = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    assert abs((result - expected).total_seconds()) < 1


def test_parse_since_weeks() -> None:
    result = _parse_since("4w")
    expected = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=28)
    assert abs((result - expected).total_seconds()) < 1


def test_parse_since_months() -> None:
    result = _parse_since("6m")
    expected = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=180)
    assert abs((result - expected).total_seconds()) < 1


def test_parse_since_years() -> None:
    result = _parse_since("1y")
    expected = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365)
    assert abs((result - expected).total_seconds()) < 1


def test_parse_since_invalid() -> None:
    with pytest.raises(ComoError, match="Invalid --since"):
        _parse_since("invalid")


def test_parse_since_invalid_unit() -> None:
    with pytest.raises(ComoError):
        _parse_since("30x")


# ---------------------------------------------------------------------------
# cmd_data with --since
# ---------------------------------------------------------------------------


def test_cmd_data_with_since_filters(db_path: Path, captured_console: StringIO) -> None:
    _seed(db_path, [(_ago(2), 5000, 40), ("2020-01-01T08:00:00", 4000, 50)])
    cmd_data(since="30d")
    assert "Entries" in captured_console.getvalue()


def test_cmd_data_since_excludes_older_rows(
    db_path: Path, captured_console: StringIO
) -> None:
    _seed(db_path, [(_ago(2), 5000, 40), (_ago(90), 4000, 50)])
    cmd_data(since="30d")
    # Only the recent row falls inside the window.
    assert "Entries:    1" in captured_console.getvalue()


def test_cmd_data_since_no_entries(db_path: Path) -> None:
    _seed(db_path, [("2020-01-01T08:00:00", 5000, 40)])
    with pytest.raises(ComoError, match="No entries"):
        cmd_data(since="1d")


def test_cmd_data_since_invalid_format(db_path: Path) -> None:
    _seed(db_path, [(_ago(1), 5000, 40)])
    with pytest.raises(ComoError, match="Invalid --since"):
        cmd_data(since="bad")
