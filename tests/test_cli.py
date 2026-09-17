import json
from pathlib import Path

import pytest

from tradeguard.cli import build_payload, main
from tradeguard.risk import RiskBudget, RiskLimits


def _journal(tmp_path: Path, rows: str, header: str = "symbol,side,entry,exit,stop_loss,quantity") -> Path:
    journal = tmp_path / "journal.csv"
    journal.write_text(header + "\n" + rows, encoding="utf-8")
    return journal


def test_build_payload_has_versioned_report_schema(tmp_path: Path):
    payload = build_payload(str(_journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert payload["metrics"]["trades"] == 1
    assert payload["metrics"]["net_pnl"] == 10.0
    assert len(payload["journal_fingerprint"]) == 64
    assert payload["diagnostics"]["valid_for_metrics"] is True
    assert payload["risk"]["exposure_basis"] == "historical_entry_notional"
    assert payload["risk"]["initial_risk"]["total_initial_risk"] == 5.0
    assert payload["segments"]["by_symbol"]["BTCUSDT"]["trades"] == 1
    assert payload["segments"]["by_side"]["long"]["net_pnl"] == 10.0
    assert "temporal" not in payload["segments"]


def test_report_contract_adds_limits_budget_and_segments_without_changing_v1(tmp_path: Path):
    journal = _journal(tmp_path, "btcusdt,long,100,110,95,2\nETHUSDT,short,50,45,55,1\n")
    payload = build_payload(str(journal), RiskLimits(max_trade_notional=150.0), RiskBudget(max_trade_initial_risk=8.0, max_total_initial_risk=12.0))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert [*payload["segments"]["by_symbol"]] == ["BTCUSDT", "ETHUSDT"]
    assert [*payload["segments"]["by_side"]] == ["long", "short"]
    assert payload["risk"]["budget"]["complete"] is True
    assert [item["code"] for item in payload["risk"]["budget"]["breaches"]] == ["max_trade_initial_risk", "max_total_initial_risk"]
    assert payload["risk"]["limits"]["max_trade_notional"] == 150.0


def test_temporal_report_is_additive_and_explicit_about_incomplete_coverage(tmp_path: Path):
    journal = _journal(
        tmp_path,
        "BTCUSDT,long,100,110,95,1,2026-09-01T09:00:00,2026-09-01T10:00:00\nETHUSDT,short,50,45,55,1,,\n",
        "symbol,side,entry,exit,stop_loss,quantity,opened_at,closed_at",
    )
    payload = build_payload(str(journal), temporal_group="day")
    temporal = payload["segments"]["temporal"]
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert temporal["basis"] == "recorded_closed_at_calendar_period"
    assert temporal["period"] == "day"
    assert temporal["complete"] is False
    assert temporal["measured_trades"] == 1
    assert list(temporal["segments"]) == ["2026-09-01"]
    assert temporal["diagnostics"][0]["code"] == "missing_closed_at"


def test_missing_stop_is_machine_readable_and_budget_incomplete(tmp_path: Path):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,1\n", "symbol,side,entry,exit,quantity")
    payload = build_payload(str(journal), budget=RiskBudget(max_total_initial_risk=10.0))
    assert payload["risk"]["initial_risk"]["diagnostics"][0]["code"] == "unusable_initial_risk"
    assert payload["risk"]["budget"]["complete"] is False
    assert payload["risk"]["budget"]["breaches"] == []


def test_cli_writes_deterministic_json_report_with_budget_and_temporal_group(tmp_path: Path, monkeypatch):
    journal = _journal(
        tmp_path,
        "BTCUSDT,long,100,110,95,1,,2026-09-01T10:00:00\nETHUSDT,long,100,95,90,1,,2026-09-02T10:00:00\n",
        "symbol,side,entry,exit,stop_loss,quantity,opened_at,closed_at",
    )
    report = tmp_path / "report.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), "--output", str(report), "--json", "--group-by-time", "day", "--max-gross-notional", "150", "--max-total-initial-risk", "12"])
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["report_schema"] == "tradeguard.report.v1"
    assert data["metrics"]["profit_factor"] == 2.0
    assert data["risk"]["breaches"][0]["code"] == "max_gross_notional"
    assert data["risk"]["budget"]["breaches"][0]["code"] == "max_total_initial_risk"
    assert list(data["segments"]["by_symbol"]) == ["BTCUSDT", "ETHUSDT"]
    assert list(data["segments"]["temporal"]["segments"]) == ["2026-09-01", "2026-09-02"]


def test_duplicate_rows_suppress_metrics_risk_and_segments(tmp_path: Path):
    row = "BTCUSDT,long,100,110,95,1\n"
    payload = build_payload(str(_journal(tmp_path, row + row)))
    assert payload["metrics"] is None
    assert payload["risk"] is None
    assert payload["segments"] is None
    assert payload["diagnostics"]["duplicate_count"] == 1


@pytest.mark.parametrize("flag", ["--max-gross-notional", "--max-symbol-gross-notional", "--max-trade-notional", "--max-trade-initial-risk", "--max-total-initial-risk"])
@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf"])
def test_cli_rejects_non_positive_or_non_finite_limits(tmp_path: Path, monkeypatch, flag, value):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), flag, value])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
