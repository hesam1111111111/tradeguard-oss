from pathlib import Path

import pytest

from tradeguard.io import load_trades_csv
from tradeguard.schema import SCHEMA_VERSION, validate_columns


def test_load_trades_csv(tmp_path: Path):
    csv_file = tmp_path / "journal.csv"
    csv_file.write_text(
        "symbol,side,entry,exit,stop_loss,quantity,opened_at,closed_at\n"
        "BTCUSDT,long,100,110,95,2,2026-01-01T10:00:00,2026-01-01T11:00:00\n",
        encoding="utf-8",
    )

    trades = load_trades_csv(csv_file)
    assert len(trades) == 1
    assert trades[0].symbol == "BTCUSDT"
    assert trades[0].quantity == 2
    assert trades[0].pnl == 20


def test_schema_reports_missing_required_columns():
    assert SCHEMA_VERSION == "1.0"
    assert validate_columns(["symbol", "entry"]) == ["side", "exit"]


def test_csv_reports_physical_row_for_invalid_number(tmp_path: Path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text(
        "symbol,side,entry,exit\nBTCUSDT,long,not-a-number,110\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="CSV row 2"):
        load_trades_csv(csv_file)
