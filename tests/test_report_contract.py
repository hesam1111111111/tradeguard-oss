from pathlib import Path

from tradeguard.cli import REPORT_SCHEMA, build_payload


def _write_journal(tmp_path: Path, header: str, rows: str) -> Path:
    path = tmp_path / "journal.csv"
    path.write_text(header + "\n" + rows, encoding="utf-8")
    return path


def test_v1_legacy_shape_remains_stable_without_temporal_request(tmp_path: Path):
    journal = _write_journal(
        tmp_path,
        "symbol,side,entry,exit,stop_loss,quantity",
        "BTCUSDT,long,100,110,95,1\n",
    )
    payload = build_payload(str(journal))

    assert REPORT_SCHEMA == "tradeguard.report.v1"
    assert payload["report_schema"] == REPORT_SCHEMA
    assert set(payload) == {
        "report_schema",
        "source",
        "journal_fingerprint",
        "metrics",
        "issues",
        "diagnostics",
        "risk",
        "segments",
    }
    assert set(payload["segments"]) == {"by_symbol", "by_side"}
    assert "by_closed_period" not in payload["segments"]


def test_v1_temporal_section_is_strictly_additive(tmp_path: Path):
    journal = _write_journal(
        tmp_path,
        "symbol,side,entry,exit,stop_loss,quantity,closed_at",
        "BTCUSDT,long,100,110,95,1,2026-09-01T10:00:00\n",
    )
    baseline = build_payload(str(journal))
    temporal = build_payload(str(journal), temporal_period="day")

    assert set(temporal) == set(baseline)
    assert temporal["metrics"] == baseline["metrics"]
    assert temporal["risk"] == baseline["risk"]
    assert temporal["segments"]["by_symbol"] == baseline["segments"]["by_symbol"]
    assert temporal["segments"]["by_side"] == baseline["segments"]["by_side"]
    assert "by_closed_period" in temporal["segments"]


def test_invalid_journal_preserves_nullable_contract(tmp_path: Path):
    journal = _write_journal(
        tmp_path,
        "symbol,side,entry,exit,stop_loss,quantity",
        "BTCUSDT,long,100,110,95,1\nBTCUSDT,long,100,110,95,1\n",
    )
    payload = build_payload(str(journal), temporal_period="day")

    assert payload["metrics"] is None
    assert payload["risk"] is None
    assert payload["segments"] is None
    assert payload["diagnostics"]["valid_for_metrics"] is False


def test_temporal_incomplete_coverage_is_explicit_not_fabricated(tmp_path: Path):
    journal = _write_journal(
        tmp_path,
        "symbol,side,entry,exit,stop_loss,quantity,closed_at",
        "BTCUSDT,long,100,110,95,1,2026-09-01T10:00:00\nETHUSDT,short,50,45,55,1,\n",
    )
    payload = build_payload(str(journal), temporal_period="month")
    temporal = payload["segments"]["by_closed_period"]

    assert temporal["basis"] == "recorded_closed_at_no_timezone_conversion"
    assert temporal["complete"] is False
    assert temporal["measured_trades"] == 1
    assert list(temporal["segments"]) == ["2026-09"]
    assert [item["code"] for item in temporal["diagnostics"]] == ["missing_closed_at"]
