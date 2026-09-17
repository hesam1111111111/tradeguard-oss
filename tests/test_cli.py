import json
from pathlib import Path

from tradeguard.cli import build_payload, main
from tradeguard.risk import RiskLimits


def test_build_payload_has_versioned_report_schema(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,1\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert payload["metrics"]["trades"] == 1
    assert payload["metrics"]["net_pnl"] == 10.0
    assert len(payload["journal_fingerprint"]) == 64
    assert payload["diagnostics"]["valid_for_metrics"] is True
    assert payload["risk"]["exposure_basis"] == "historical_entry_notional"
    assert payload["risk"]["initial_risk"]["total_initial_risk"] == 5.0


def test_report_contract_adds_risk_without_changing_v1_schema(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,2\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal), RiskLimits(max_trade_notional=150.0))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert payload["risk"]["exposures"][0]["gross_notional"] == 200.0
    assert payload["risk"]["initial_risk"]["measured_trades"] == 1
    assert [item["code"] for item in payload["risk"]["breaches"]] == ["max_trade_notional"]
    assert payload["risk"]["limits"]["max_trade_notional"] == 150.0


def test_missing_stop_is_machine_readable_initial_risk_diagnostic(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "symbol,side,entry,exit,quantity\nBTCUSDT,long,100,110,1\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal))
    initial = payload["risk"]["initial_risk"]
    assert initial["measured_trades"] == 0
    assert initial["diagnostics"][0]["code"] == "unusable_initial_risk"


def test_cli_writes_deterministic_json_report(tmp_path: Path, monkeypatch):
    journal = tmp_path / "journal.csv"
    report = tmp_path / "report.json"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity\n"
        "BTCUSDT,long,100,110,95,1\n"
        "ETHUSDT,long,100,95,90,1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["tradeguard", str(journal), "--output", str(report), "--json", "--max-gross-notional", "150"],
    )
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["report_schema"] == "tradeguard.report.v1"
    assert data["metrics"]["profit_factor"] == 2.0
    assert data["diagnostics"]["duplicate_count"] == 0
    assert data["risk"]["limits"]["max_gross_notional"] == 150.0
    assert data["risk"]["breaches"][0]["code"] == "max_gross_notional"


def test_duplicate_rows_suppress_metrics_and_risk(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    row = "BTCUSDT,long,100,110,95,1\n"
    journal.write_text("symbol,side,entry,exit,stop_loss,quantity\n" + row + row, encoding="utf-8")
    payload = build_payload(str(journal))
    assert payload["metrics"] is None
    assert payload["risk"] is None
    assert payload["diagnostics"]["duplicate_count"] == 1
    assert payload["diagnostics"]["valid_for_metrics"] is False
