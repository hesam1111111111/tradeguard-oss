from pathlib import Path

from tradeguard.io import load_trades_csv


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
