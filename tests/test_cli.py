"""CLI integration tests using Click's test runner."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

import como.core
from como import __version__
from como.battery import BatteryInfo
from como.cli import main
from como.core import _open_db

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
    path = tmp_path / "como.db"
    monkeypatch.setattr(como.core, "COMO_BATTERY_FILE", path)
    return path


def _ago(days: int) -> str:
    """Timestamp `days` in the past, so --since tests never go stale."""
    ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _seed(db_path: Path, rows: Sequence[tuple[str, int, int | None]]) -> None:
    conn = _open_db(db_path)
    try:
        for row in rows:
            conn.execute(
                "INSERT INTO battery (time, capacity, cycles) VALUES (?, ?, ?)", row
            )
        conn.commit()
    finally:
        conn.close()


def test_version() -> None:
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_default_runs_save(db_path: Path) -> None:
    with patch("como.core.get_battery", return_value=_SAMPLE_BATTERY):
        result = CliRunner().invoke(main, [])
    assert result.exit_code == 0
    assert db_path.exists()


def test_save(db_path: Path) -> None:
    with patch("como.core.get_battery", return_value=_SAMPLE_BATTERY):
        result = CliRunner().invoke(main, ["save"])
    assert result.exit_code == 0
    assert db_path.exists()


def test_save_twice_appends(db_path: Path) -> None:
    _seed(db_path, [("2024-01-01T08:00:00", 5000, 42)])
    with patch("como.core.get_battery", return_value=_SAMPLE_BATTERY):
        CliRunner().invoke(main, ["save"])

    import sqlite3

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM battery").fetchone()[0]
    conn.close()
    assert count == 2


def test_data_no_db(db_path: Path) -> None:
    result = CliRunner().invoke(main, ["data"])
    assert result.exit_code == 1


def test_data_with_db(db_path: Path) -> None:
    rows = [(f"2024-01-0{i + 1}T08:00:00", 5000 - i * 100, 40 + i) for i in range(3)]
    _seed(db_path, rows)
    result = CliRunner().invoke(main, ["data"])
    assert result.exit_code == 0


def test_reset_confirmed(db_path: Path) -> None:
    _open_db(db_path).close()
    result = CliRunner().invoke(main, ["reset"], input="y\n")
    assert result.exit_code == 0
    assert not db_path.exists()


def test_reset_cancelled(db_path: Path) -> None:
    _open_db(db_path).close()
    result = CliRunner().invoke(main, ["reset"], input="n\n")
    assert result.exit_code == 0
    assert db_path.exists()


def test_export(db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed(db_path, [("2024-01-01T08:00:00", 5000, 42)])
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["export"])
    assert result.exit_code == 0
    assert (tmp_path / "como.csv").exists()


def test_import_from_csv(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    csv_content = "time,capacity,cycles\n2024-01-01T08:00:00,5000,42\n"
    csv_file = tmp_path / "import.csv"
    csv_file.write_text(csv_content)

    result = CliRunner().invoke(main, ["import", str(csv_file)])
    assert result.exit_code == 0
    assert db_path.exists()


def test_import_legacy_csv(db_path: Path, tmp_path: Path) -> None:
    csv_content = "date,capacity,loadcycles\n2024-01-01,5000,42\n"
    csv_file = tmp_path / "legacy.csv"
    csv_file.write_text(csv_content)

    result = CliRunner().invoke(main, ["import", str(csv_file)])
    assert result.exit_code == 0

    import sqlite3

    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT time, capacity, cycles FROM battery").fetchone()
    conn.close()
    assert row[0] == "2024-01-01T00:00:00"
    assert row[1] == 5000
    assert row[2] == 42


def test_info(db_path: Path) -> None:
    with patch("como.core.get_batteries", return_value=[_SAMPLE_BATTERY]):
        result = CliRunner().invoke(main, ["info"])
    assert result.exit_code == 0


def test_data_with_since(db_path: Path) -> None:
    _seed(db_path, [(_ago(2), 5000, 40), ("2020-01-01T08:00:00", 4000, 50)])
    result = CliRunner().invoke(main, ["data", "--since", "30d"])
    assert result.exit_code == 0


def test_data_invalid_since(db_path: Path) -> None:
    _seed(db_path, [(_ago(2), 5000, 40)])
    result = CliRunner().invoke(main, ["data", "--since", "invalid"])
    assert result.exit_code == 1


def test_data_since_no_entries(db_path: Path) -> None:
    _seed(db_path, [("2020-01-01T08:00:00", 5000, 40)])
    result = CliRunner().invoke(main, ["data", "--since", "1d"])
    assert result.exit_code == 1
