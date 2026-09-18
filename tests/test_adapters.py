from pathlib import Path

import pytest

from tradeguard import available_import_profiles, get_import_profile, import_csv_with_profile
from tradeguard.io import load_trades_csv


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_profiles_are_stable_and_explicit():
    assert available_import_profiles() == ("generic_ohlc", "generic_ticket_export")
    assert dict(get_import_profile("generic_ticket_export"))["entry"] == "OpenPrice"


def test_unknown_profile_fails_closed():
    with pytest.raises(ValueError, match="Unknown import profile: guessed-broker"):
        get_import_profile("guessed-broker")


def test_ticket_profile_matches_canonical_csv(tmp_path: Path):
    source = _write(
        tmp_path / "ticket.csv",
        "Ticker,Direction,OpenPrice,ClosePrice,Stop,Size,OpenTime,CloseTime\n"
        "BTCUSDT,long,100,110,95,2,2026-09-01T09:00:00,2026-09-01T10:00:00\n",
    )
    canonical = _write(
        tmp_path / "canonical.csv",
        "symbol,side,entry,exit,stop_loss,quantity,opened_at,closed_at\n"
        "BTCUSDT,long,100,110,95,2,2026-09-01T09:00:00,2026-09-01T10:00:00\n",
    )
    result = import_csv_with_profile(str(source), "generic_ticket_export")
    assert result.complete is True
    assert result.trades == tuple(load_trades_csv(canonical))
