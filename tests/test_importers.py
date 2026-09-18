from pathlib import Path

import pytest

from tradeguard.analytics import analyze_trades
from tradeguard.importers import import_mapped_csv
from tradeguard.io import load_trades_csv


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_import_mapped_csv_matches_equivalent_native_csv(tmp_path: Path):
    source = _write(
        tmp_path / "external.csv",
        "ticker,direction,open_px,close_px,stop,qty,opened,closed\n"
        "BTCUSDT,long,100,110,95,2,2026-09-01T09:00:00,2026-09-01T10:00:00\n"
        "ETHUSDT,short,50,45,55,1,2026-09-02T09:00:00,2026-09-02T10:00:00\n",
    )
    native = _write(
        tmp_path / "native.csv",
        "symbol,side,entry,exit,stop_loss,quantity,opened_at,closed_at\n"
        "BTCUSDT,long,100,110,95,2,2026-09-01T09:00:00,2026-09-01T10:00:00\n"
        "ETHUSDT,short,50,45,55,1,2026-09-02T09:00:00,2026-09-02T10:00:00\n",
    )
    mapping = {
        "symbol": "ticker",
        "side": "direction",
        "entry": "open_px",
        "exit": "close_px",
        "stop_loss": "stop",
        "quantity": "qty",
        "opened_at": "opened",
        "closed_at": "closed",
    }
    result = import_mapped_csv(source, mapping)
    native_trades = load_trades_csv(native)
    assert result.source_rows == 2
    assert result.imported_rows == 2
    assert result.rejected_rows == 0
    assert result.complete is True
    assert result.trades == tuple(native_trades)
    assert analyze_trades(result.trades) == analyze_trades(native_trades)


def test_import_mapped_csv_rejects_invalid_rows_explicitly(tmp_path: Path):
    source = _write(
        tmp_path / "external.csv",
        "ticker,direction,open_px,close_px\n"
        "BTCUSDT,long,100,110\n"
        "ETHUSDT,short,not-a-number,45\n",
    )
    result = import_mapped_csv(
        source,
        {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px"},
    )
    assert result.source_rows == 2
    assert result.imported_rows == 1
    assert result.rejected_rows == 1
    assert result.source_rows == result.imported_rows + result.rejected_rows
    assert result.complete is False
    assert result.diagnostics[0].code == "invalid_number"
    assert result.diagnostics[0].field == "entry"
    assert result.diagnostics[0].value == "not-a-number"
    assert result.diagnostics[0].source_row == 3


def test_import_mapped_csv_requires_explicit_required_mappings(tmp_path: Path):
    source = _write(tmp_path / "external.csv", "ticker,direction,open_px\nBTCUSDT,long,100\n")
    with pytest.raises(ValueError, match="Missing required canonical mappings: exit"):
        import_mapped_csv(source, {"symbol": "ticker", "side": "direction", "entry": "open_px"})


def test_import_mapped_csv_fails_when_mapped_source_column_is_absent(tmp_path: Path):
    source = _write(tmp_path / "external.csv", "ticker,direction,open_px,close_px\nBTCUSDT,long,100,110\n")
    with pytest.raises(ValueError, match="Missing mapped source columns: missing_column"):
        import_mapped_csv(
            source,
            {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "missing_column"},
        )


def test_import_mapping_rejects_unknown_or_duplicate_source_columns(tmp_path: Path):
    source = _write(tmp_path / "external.csv", "ticker,direction,open_px,close_px\nBTCUSDT,long,100,110\n")
    with pytest.raises(ValueError, match="Unknown canonical mapping fields: price"):
        import_mapped_csv(
            source,
            {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px", "price": "x"},
        )
    with pytest.raises(ValueError, match="Each source column may map to only one canonical field"):
        import_mapped_csv(
            source,
            {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "open_px"},
        )


def test_import_mapped_csv_reports_field_level_diagnostics(tmp_path: Path):
    source = _write(
        tmp_path / "external.csv",
        "ticker,direction,open_px,close_px,opened\n"
        "BTCUSDT,long,bad,110,not-a-date\n"
        ",short,50,45,2026-09-01T10:00:00\n",
    )
    result = import_mapped_csv(
        source,
        {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px", "opened_at": "opened"},
    )
    assert result.rejected_rows == 2
    assert [(d.code, d.source_row, d.field) for d in result.diagnostics] == [
        ("invalid_number", 2, "entry"),
        ("invalid_datetime", 2, "opened_at"),
        ("missing_required_value", 3, "symbol"),
    ]
    assert result.diagnostics[0].value == "bad"


def test_import_diagnostics_use_canonical_order_and_ignore_blank_numeric_duplicates(tmp_path: Path):
    source = _write(
        tmp_path / "external.csv",
        "ticker,direction,open_px,close_px,stop,qty,opened,closed\n"
        "BTCUSDT,long,   ,bad-stop,bad-stop,bad-qty,bad-opened,bad-closed\n",
    )
    result = import_mapped_csv(
        source,
        {
            "symbol": "ticker",
            "side": "direction",
            "entry": "open_px",
            "exit": "close_px",
            "stop_loss": "stop",
            "quantity": "qty",
            "opened_at": "opened",
            "closed_at": "closed",
        },
    )
    assert [(d.code, d.field) for d in result.diagnostics] == [
        ("missing_required_value", "entry"),
        ("invalid_number", "exit"),
        ("invalid_number", "stop_loss"),
        ("invalid_number", "quantity"),
        ("invalid_datetime", "opened_at"),
        ("invalid_datetime", "closed_at"),
    ]
    assert sum(d.field == "entry" for d in result.diagnostics) == 1


def test_import_mapped_csv_rejects_duplicate_source_headers(tmp_path: Path):
    source = _write(
        tmp_path / "duplicate_headers.csv",
        "ticker,direction,open_px,open_px,close_px\nBTCUSDT,long,100,101,110\n",
    )
    with pytest.raises(ValueError, match="Duplicate source CSV columns: open_px"):
        import_mapped_csv(
            source,
            {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px"},
        )


def test_import_mapped_csv_rejects_rows_with_unexpected_extra_values(tmp_path: Path):
    source = _write(
        tmp_path / "extra_values.csv",
        "ticker,direction,open_px,close_px\nBTCUSDT,long,100,110,unexpected\nETHUSDT,short,50,45\n",
    )
    result = import_mapped_csv(
        source,
        {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px"},
    )
    assert result.source_rows == 2
    assert result.imported_rows == 1
    assert result.rejected_rows == 1
    assert result.complete is False
    assert [(d.code, d.source_row, d.value) for d in result.diagnostics] == [
        ("unexpected_extra_values", 2, "unexpected"),
    ]
