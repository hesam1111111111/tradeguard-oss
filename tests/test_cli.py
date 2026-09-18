import json
from pathlib import Path

import pytest

from tradeguard.cli import build_payload, main
from tradeguard.risk import RiskBudget, RiskLimits


def _journal(tmp_path: Path, rows: str) -> Path:
    journal = tmp_path / "journal.csv"
    journal.write_text("symbol,side,entry,exit,stop_loss,quantity\n" + rows, encoding="utf-8")
    return journal


def test_build_payload_has_versioned_report_schema(tmp_path: Path):
    payload = build_payload(str(_journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert payload["import"] is None
    assert payload["metrics"]["trades"] == 1
    assert payload["metrics"]["net_pnl"] == 10.0
    assert len(payload["journal_fingerprint"]) == 64
    assert payload["diagnostics"]["valid_for_metrics"] is True
    assert payload["risk"]["exposure_basis"] == "historical_entry_notional"
    assert payload["risk"]["initial_risk"]["total_initial_risk"] == 5.0
    assert payload["segments"]["by_symbol"]["BTCUSDT"]["trades"] == 1
    assert payload["segments"]["by_side"]["long"]["net_pnl"] == 10.0
    assert "by_closed_period" not in payload["segments"]


def test_report_contract_adds_limits_budget_and_segments_without_changing_v1(tmp_path: Path):
    journal = _journal(tmp_path, "btcusdt,long,100,110,95,2\nETHUSDT,short,50,45,55,1\n")
    payload = build_payload(str(journal), RiskLimits(max_trade_notional=150.0), RiskBudget(max_trade_initial_risk=8.0, max_total_initial_risk=12.0))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert [*payload["segments"]["by_symbol"]] == ["BTCUSDT", "ETHUSDT"]
    assert [*payload["segments"]["by_side"]] == ["long", "short"]
    assert payload["risk"]["budget"]["complete"] is True
    assert [item["code"] for item in payload["risk"]["budget"]["breaches"]] == ["max_trade_initial_risk", "max_total_initial_risk"]
    assert payload["risk"]["limits"]["max_trade_notional"] == 150.0


def test_mapped_import_adds_provenance_and_preserves_analytics(tmp_path: Path):
    source = tmp_path / "external.csv"
    source.write_text("ticker,direction,open_px,close_px,qty\nBTCUSDT,long,100,110,2\n", encoding="utf-8")
    payload = build_payload(
        str(source),
        import_mapping={"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px", "quantity": "qty"},
    )
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert payload["import"] == {
        "mode": "explicit_mapped_csv",
        "complete": True,
        "source_rows": 1,
        "imported_rows": 1,
        "rejected_rows": 0,
        "mapping": {"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px", "quantity": "qty"},
        "diagnostics": [],
    }
    assert payload["metrics"]["net_pnl"] == 20.0


def test_mapped_import_rejections_are_explicit_and_suppress_partial_metrics(tmp_path: Path):
    source = tmp_path / "external.csv"
    source.write_text("ticker,direction,open_px,close_px\nBTCUSDT,long,100,110\nETHUSDT,short,bad,90\n", encoding="utf-8")
    payload = build_payload(
        str(source),
        import_mapping={"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px"},
    )
    assert payload["import"]["source_rows"] == 2
    assert payload["import"]["imported_rows"] == 1
    assert payload["import"]["rejected_rows"] == 1
    assert payload["import"]["complete"] is False
    assert payload["import"]["diagnostics"][0]["source_row"] == 3
    assert payload["metrics"] is None
    assert payload["risk"] is None
    assert payload["segments"] is None


def test_temporal_grouping_is_additive_and_machine_readable(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity,closed_at\n"
        "BTCUSDT,long,100,110,95,1,2026-09-01T10:00:00\n"
        "ETHUSDT,short,50,45,55,1,2026-09-02T11:00:00\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal), temporal_period="day")
    temporal = payload["segments"]["by_closed_period"]
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert temporal["basis"] == "recorded_closed_at_no_timezone_conversion"
    assert temporal["period"] == "day"
    assert temporal["complete"] is True
    assert temporal["measured_trades"] == 2
    assert list(temporal["segments"]) == ["2026-09-01", "2026-09-02"]
    assert sum(item["net_pnl"] for item in temporal["segments"].values()) == payload["metrics"]["net_pnl"]
    assert temporal["diagnostics"] == []


def test_temporal_grouping_keeps_missing_timestamp_explicit(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity,closed_at\n"
        "BTCUSDT,long,100,110,95,1,2026-09-01T10:00:00\n"
        "ETHUSDT,short,50,45,55,1,\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal), temporal_period="month")
    temporal = payload["segments"]["by_closed_period"]
    assert temporal["complete"] is False
    assert temporal["measured_trades"] == 1
    assert list(temporal["segments"]) == ["2026-09"]
    assert temporal["diagnostics"][0]["code"] == "missing_closed_at"
    assert temporal["diagnostics"][0]["trade_index"] == 1


def test_missing_stop_is_machine_readable_and_budget_incomplete(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text("symbol,side,entry,exit,quantity\nBTCUSDT,long,100,110,1\n", encoding="utf-8")
    payload = build_payload(str(journal), budget=RiskBudget(max_total_initial_risk=10.0))
    assert payload["risk"]["initial_risk"]["diagnostics"][0]["code"] == "unusable_initial_risk"
    assert payload["risk"]["budget"]["complete"] is False
    assert payload["risk"]["budget"]["breaches"] == []


def test_cli_writes_deterministic_json_report_with_budget(tmp_path: Path, monkeypatch):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\nETHUSDT,long,100,95,90,1\n")
    report = tmp_path / "report.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), "--output", str(report), "--json", "--max-gross-notional", "150", "--max-total-initial-risk", "12"])
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["report_schema"] == "tradeguard.report.v1"
    assert data["metrics"]["profit_factor"] == 2.0
    assert data["risk"]["breaches"][0]["code"] == "max_gross_notional"
    assert data["risk"]["budget"]["breaches"][0]["code"] == "max_total_initial_risk"
    assert list(data["segments"]["by_symbol"]) == ["BTCUSDT", "ETHUSDT"]


def test_cli_mapped_import_writes_provenance(tmp_path: Path, monkeypatch):
    source = tmp_path / "external.csv"
    source.write_text("ticker,direction,open_px,close_px\nBTCUSDT,long,100,110\n", encoding="utf-8")
    report = tmp_path / "report.json"
    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(source), "--output", str(report),
        "--map", "symbol=ticker", "--map", "side=direction", "--map", "entry=open_px", "--map", "exit=close_px",
    ])
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["import"]["complete"] is True
    assert data["import"]["mapping"]["symbol"] == "ticker"
    assert data["metrics"]["net_pnl"] == 10.0


def test_cli_group_closed_by_writes_temporal_section(tmp_path: Path, monkeypatch):
    journal = tmp_path / "journal.csv"
    journal.write_text("symbol,side,entry,exit,stop_loss,quantity,closed_at\nBTCUSDT,long,100,110,95,1,2026-09-01T10:00:00\n", encoding="utf-8")
    report = tmp_path / "report.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), "--output", str(report), "--group-closed-by", "month"])
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["segments"]["by_closed_period"]["period"] == "month"
    assert list(data["segments"]["by_closed_period"]["segments"]) == ["2026-09"]


def test_duplicate_rows_suppress_metrics_risk_and_segments(tmp_path: Path):
    row = "BTCUSDT,long,100,110,95,1\n"
    payload = build_payload(str(_journal(tmp_path, row + row)), temporal_period="day")
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


def test_cli_reconciliation_writes_stable_audit_json(tmp_path: Path, monkeypatch):
    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    header = "symbol,side,entry,exit,stop_loss,quantity\n"
    reference.write_text(header + "BTCUSDT,long,100,110,95,1\n", encoding="utf-8")
    candidate.write_text(header + "BTCUSDT,long,100,108,95,1\n", encoding="utf-8")
    report = tmp_path / "reconciliation.json"
    monkeypatch.setattr(
        "sys.argv",
        ["tradeguard", str(reference), "--reconcile-with", str(candidate), "--output", str(report), "--json"],
    )
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["reconciliation_schema"] == "tradeguard.reconciliation.v1"
    assert data["clean"] is False
    assert data["modified_rows"] == 1
    assert data["mismatches"][0]["field"] == "exit"
    assert len(data["reference_fingerprint"]) == 64
    assert len(data["candidate_fingerprint"]) == 64


def test_cli_reconciliation_fail_on_drift_is_ci_friendly(tmp_path: Path, monkeypatch):
    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    header = "symbol,side,entry,exit\n"
    reference.write_text(header + "BTCUSDT,long,100,110\n", encoding="utf-8")
    candidate.write_text(header + "BTCUSDT,long,100,109\n", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["tradeguard", str(reference), "--reconcile-with", str(candidate), "--fail-on-drift"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_cli_writes_trial_evidence_bundle(tmp_path: Path, monkeypatch):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    evidence = tmp_path / "evidence.json"
    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(journal), "--evidence-output", str(evidence),
        "--run-id", "oos-0042", "--max-total-initial-risk", "20",
    ])
    main()
    data = json.loads(evidence.read_text(encoding="utf-8"))
    assert data["trial_ledger_schema"] == "tradeguard.trial-ledger.v1"
    assert data["run_id"] == "oos-0042"
    assert data["configuration"]["risk_budget"]["max_total_initial_risk"] == 20.0
    assert len(data["evidence_fingerprint"]) == 64


def test_cli_trial_evidence_requires_explicit_run_id(tmp_path: Path, monkeypatch):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), "--evidence-output", str(tmp_path / "e.json")])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_cli_writes_and_verifies_certification_bundle(tmp_path: Path, monkeypatch):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    evidence = tmp_path / "evidence.json"
    certification = tmp_path / "certification.json"
    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(journal), "--evidence-output", str(evidence),
        "--certification-output", str(certification), "--run-id", "oos-0042",
    ])
    main()
    data = json.loads(certification.read_text(encoding="utf-8"))
    assert data["evidence_bundle_schema"] == "tradeguard.evidence-bundle.v1"
    assert data["certification"]["status"] == "PASS"
    assert len(data["bundle_fingerprint"]) == 64

    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(journal), "--verify-certification", str(certification),
    ])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_cli_verification_fails_for_tampered_bundle(tmp_path: Path, monkeypatch):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    evidence = tmp_path / "evidence.json"
    certification = tmp_path / "certification.json"
    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(journal), "--evidence-output", str(evidence),
        "--certification-output", str(certification), "--run-id", "run-1",
    ])
    main()
    data = json.loads(certification.read_text(encoding="utf-8"))
    data["evidence"]["metrics"]["net_pnl"] = 999999
    certification.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(journal), "--verify-certification", str(certification),
    ])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_cli_import_preview_reports_rejections_without_running_analytics(tmp_path: Path, monkeypatch):
    source = tmp_path / "external.csv"
    source.write_text(
        "ticker,direction,open_px,close_px\nBTCUSDT,long,100,110\nETHUSDT,short,bad,45\n",
        encoding="utf-8",
    )
    output = tmp_path / "preview.json"
    monkeypatch.setattr("sys.argv", [
        "tradeguard", str(source), "--import-preview", "--output", str(output),
        "--map", "symbol=ticker", "--map", "side=direction", "--map", "entry=open_px", "--map", "exit=close_px",
    ])
    main()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["preview"] is True
    assert data["source_rows"] == 2
    assert data["imported_rows"] == 1
    assert data["rejected_rows"] == 1
    assert data["diagnostics"][0]["code"] == "invalid_number"
    assert "metrics" not in data


def test_cli_verification_passes_without_csv_path(tmp_path: Path, monkeypatch):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    evidence = tmp_path / "evidence.json"
    certification = tmp_path / "certification.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), "--evidence-output", str(evidence), "--certification-output", str(certification), "--run-id", "run-pass"])
    main()
    monkeypatch.setattr("sys.argv", ["tradeguard", "--verify-certification", str(certification)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_cli_verification_fails_for_valid_fail_certification(tmp_path: Path, monkeypatch):
    from tradeguard.certification import build_evidence_bundle
    from tradeguard.evidence import build_trial_evidence

    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    report = build_payload(str(journal))
    evidence = build_trial_evidence("run-fail", report, parent_evidence_fingerprint="a" * 64)
    bundle = build_evidence_bundle(evidence, expected_parent_fingerprint="b" * 64)
    assert bundle["certification"]["status"] == "FAIL"
    certification = tmp_path / "fail-certification.json"
    certification.write_text(json.dumps(bundle), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["tradeguard", "--verify-certification", str(certification)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_cli_verification_fails_closed_for_non_object_json(tmp_path: Path, monkeypatch):
    certification = tmp_path / "not-object.json"
    certification.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["tradeguard", "--verify-certification", str(certification)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
