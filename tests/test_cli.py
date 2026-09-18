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


def _ticket_profile_csv(tmp_path: Path) -> Path:
    source = tmp_path / "ticket-profile.csv"
    source.write_text(
        "Ticker,Direction,OpenPrice,ClosePrice,Stop,Size,OpenTime,CloseTime\n"
        "BTCUSDT,long,100,110,95,2,2026-09-01T09:00:00,2026-09-01T10:00:00\n",
        encoding="utf-8",
    )
    return source


def test_cli_import_profile_writes_explicit_provenance(tmp_path: Path, monkeypatch):
    source = _ticket_profile_csv(tmp_path)
    report = tmp_path / "profile-report.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(source), "--import-profile", "generic_ticket_export", "--output", str(report)])
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["import"]["mode"] == "explicit_profile_csv"
    assert data["import"]["profile"] == "generic_ticket_export"
    assert data["import"]["mapping"]["entry"] == "OpenPrice"
    assert data["metrics"]["net_pnl"] == 20.0


def test_cli_import_profile_preview_is_read_only(tmp_path: Path, monkeypatch):
    source = _ticket_profile_csv(tmp_path)
    output = tmp_path / "profile-preview.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(source), "--import-profile", "generic_ticket_export", "--import-preview", "--output", str(output)])
    main()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["preview"] is True
    assert data["profile"] == "generic_ticket_export"
    assert data["imported_rows"] == 1
    assert "metrics" not in data


def test_cli_rejects_profile_and_map_combination(tmp_path: Path, monkeypatch):
    source = _ticket_profile_csv(tmp_path)
    monkeypatch.setattr("sys.argv", ["tradeguard", str(source), "--import-profile", "generic_ticket_export", "--map", "symbol=Ticker"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_cli_unknown_import_profile_fails_closed(tmp_path: Path, monkeypatch):
    source = _ticket_profile_csv(tmp_path)
    monkeypatch.setattr("sys.argv", ["tradeguard", str(source), "--import-profile", "guessed-broker"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_cli_trial_evidence_records_selected_import_profile(tmp_path: Path, monkeypatch):
    source = _ticket_profile_csv(tmp_path)
    evidence = tmp_path / "profile-evidence.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(source), "--import-profile", "generic_ticket_export", "--evidence-output", str(evidence), "--run-id", "profile-run"])
    main()
    data = json.loads(evidence.read_text(encoding="utf-8"))
    assert data["configuration"]["import_profile"] == "generic_ticket_export"
    assert data["configuration"]["import_mapping"] is None
    assert data["import"]["mode"] == "explicit_profile_csv"


def test_cli_lists_import_profiles_without_csv(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["tradeguard", "--list-import-profiles", "--json"])
    main()
    data = json.loads(capsys.readouterr().out)
    assert data == {"profiles": ["generic_ohlc", "generic_ticket_export"]}


def test_cli_describes_import_profile_without_csv(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["tradeguard", "--describe-import-profile", "generic_ticket_export", "--json"])
    main()
    data = json.loads(capsys.readouterr().out)
    assert data["profile"] == "generic_ticket_export"
    assert data["mapping"]["symbol"] == "Ticker"
    assert data["mapping"]["closed_at"] == "CloseTime"


def test_cli_profile_introspection_unknown_profile_fails_closed(monkeypatch):
    monkeypatch.setattr("sys.argv", ["tradeguard", "--describe-import-profile", "unknown"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_cli_profile_introspection_rejects_csv_path(tmp_path: Path, monkeypatch):
    source = _ticket_profile_csv(tmp_path)
    monkeypatch.setattr("sys.argv", ["tradeguard", str(source), "--list-import-profiles"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_report_source_fingerprint_hashes_exact_file_bytes(tmp_path: Path):
    journal = _journal(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    payload = build_payload(str(journal))
    import hashlib
    assert payload["source_fingerprint"] == hashlib.sha256(journal.read_bytes()).hexdigest()
    assert len(payload["source_fingerprint"]) == 64


def test_reconciliation_binds_exact_source_artifacts_without_changing_semantic_result(tmp_path: Path):
    import hashlib
    from tradeguard.cli import _reconciliation_payload

    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    logical = "symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,1\n"
    reference.write_bytes(logical.encode("utf-8"))
    candidate.write_bytes(logical.replace("\n", "\r\n").encode("utf-8"))

    payload = _reconciliation_payload(str(reference), str(candidate))

    assert payload["reconciliation_schema"] == "tradeguard.reconciliation.v1"
    assert payload["clean"] is True
    assert payload["reference_fingerprint"] == payload["candidate_fingerprint"]
    assert payload["reference_source_fingerprint"] == hashlib.sha256(reference.read_bytes()).hexdigest()
    assert payload["candidate_source_fingerprint"] == hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert payload["reference_source_fingerprint"] != payload["candidate_source_fingerprint"]


def test_cli_reconciliation_evidence_verification_detects_tampering(tmp_path: Path, monkeypatch):
    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    header = "symbol,side,entry,exit\n"
    reference.write_text(header + "BTCUSDT,long,100,110\n", encoding="utf-8")
    candidate.write_text(header + "BTCUSDT,long,100,109\n", encoding="utf-8")
    output = tmp_path / "reconciliation.json"
    monkeypatch.setattr("sys.argv", ["tradeguard", str(reference), "--reconcile-with", str(candidate), "--output", str(output)])
    main()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data["reconciliation_evidence_fingerprint"]) == 64

    monkeypatch.setattr("sys.argv", ["tradeguard", "--verify-reconciliation", str(output)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0

    data["candidate_source_fingerprint"] = "0" * 64
    output.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["tradeguard", "--verify-reconciliation", str(output)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_cli_reconciliation_verification_fails_closed_for_non_object_json(tmp_path: Path, monkeypatch):
    output = tmp_path / "invalid-reconciliation.json"
    output.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["tradeguard", "--verify-reconciliation", str(output)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_reconciliation_verifier_rejects_logically_inconsistent_signed_payload(tmp_path: Path):
    from tradeguard.cli import _reconciliation_payload
    from tradeguard.reconciliation_evidence import sign_reconciliation_evidence, verify_reconciliation_evidence

    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    header = "symbol,side,entry,exit\n"
    reference.write_text(header + "BTCUSDT,long,100,110\n", encoding="utf-8")
    candidate.write_text(header + "BTCUSDT,long,100,109\n", encoding="utf-8")

    valid = _reconciliation_payload(str(reference), str(candidate))
    unsigned = dict(valid)
    unsigned.pop("reconciliation_evidence_fingerprint")
    unsigned["clean"] = True

    with pytest.raises(ValueError, match="reconciliation evidence violates"):
        sign_reconciliation_evidence(unsigned)

    valid["clean"] = True
    assert not verify_reconciliation_evidence(valid)


def test_reconciliation_verifier_rejects_invalid_digest_and_negative_counts(tmp_path: Path):
    from tradeguard.cli import _reconciliation_payload
    from tradeguard.reconciliation_evidence import sign_reconciliation_evidence

    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    header = "symbol,side,entry,exit\n"
    reference.write_text(header + "BTCUSDT,long,100,110\n", encoding="utf-8")
    candidate.write_text(header + "BTCUSDT,long,100,110\n", encoding="utf-8")

    payload = _reconciliation_payload(str(reference), str(candidate))
    unsigned = dict(payload)
    unsigned.pop("reconciliation_evidence_fingerprint")

    broken_digest = dict(unsigned)
    broken_digest["reference_fingerprint"] = "g" * 64
    with pytest.raises(ValueError):
        sign_reconciliation_evidence(broken_digest)

    broken_count = dict(unsigned)
    broken_count["reference_rows"] = -1
    with pytest.raises(ValueError):
        sign_reconciliation_evidence(broken_count)


def test_reconciliation_verifier_rejects_malformed_delta_and_mismatch_shapes(tmp_path: Path):
    from tradeguard.cli import _reconciliation_payload
    from tradeguard.reconciliation_evidence import sign_reconciliation_evidence

    reference = tmp_path / "reference.csv"
    candidate = tmp_path / "candidate.csv"
    header = "symbol,side,entry,exit\n"
    reference.write_text(header + "BTCUSDT,long,100,110\n", encoding="utf-8")
    candidate.write_text(header + "BTCUSDT,long,100,109\n", encoding="utf-8")

    payload = _reconciliation_payload(str(reference), str(candidate))
    unsigned = dict(payload)
    unsigned.pop("reconciliation_evidence_fingerprint")

    malformed_delta = dict(unsigned)
    malformed_delta["missing"] = [{"record": {}, "count": 0}]
    with pytest.raises(ValueError):
        sign_reconciliation_evidence(malformed_delta)

    malformed_mismatch = dict(unsigned)
    malformed_mismatch["mismatches"] = [{"identity": {}, "field": ""}]
    with pytest.raises(ValueError):
        sign_reconciliation_evidence(malformed_mismatch)
