from copy import deepcopy

import pytest

from tradeguard.cli import build_payload
from tradeguard.evidence import TRIAL_LEDGER_SCHEMA, build_trial_evidence, verify_trial_evidence


def _report(tmp_path, rows):
    path = tmp_path / "journal.csv"
    path.write_text("symbol,side,entry,exit,stop_loss,quantity\n" + rows, encoding="utf-8")
    return build_payload(str(path))


def test_trial_evidence_is_deterministic_for_same_semantic_input(tmp_path):
    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    first = build_trial_evidence("oos-0042", report, configuration={"stage": "oos"})
    second = build_trial_evidence("oos-0042", report, configuration={"stage": "oos"})
    assert first == second
    assert first["trial_ledger_schema"] == TRIAL_LEDGER_SCHEMA
    assert len(first["evidence_fingerprint"]) == 64
    assert verify_trial_evidence(first)


def test_material_configuration_change_changes_evidence_fingerprint(tmp_path):
    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    first = build_trial_evidence("run-1", report, configuration={"stage": "backtest"})
    second = build_trial_evidence("run-1", report, configuration={"stage": "oos"})
    assert first["evidence_fingerprint"] != second["evidence_fingerprint"]


def test_material_journal_change_changes_evidence_fingerprint(tmp_path):
    first_report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    first = build_trial_evidence("run-1", first_report)
    second_report = _report(tmp_path, "BTCUSDT,long,100,111,95,1\n")
    second = build_trial_evidence("run-1", second_report)
    assert first["journal_fingerprint"] != second["journal_fingerprint"]
    assert first["evidence_fingerprint"] != second["evidence_fingerprint"]


def test_parent_link_forms_verifiable_chain(tmp_path):
    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    parent = build_trial_evidence("backtest-1", report)
    child = build_trial_evidence(
        "oos-1",
        report,
        configuration={"stage": "oos"},
        parent_evidence_fingerprint=parent["evidence_fingerprint"],
    )
    assert verify_trial_evidence(child, expected_parent_fingerprint=parent["evidence_fingerprint"])
    assert not verify_trial_evidence(child, expected_parent_fingerprint="0" * 64)


def test_tampering_invalidates_evidence(tmp_path):
    evidence = build_trial_evidence("run-1", _report(tmp_path, "BTCUSDT,long,100,110,95,1\n"))
    tampered = deepcopy(evidence)
    tampered["metrics"]["net_pnl"] = 999999
    assert not verify_trial_evidence(tampered)


def test_invalid_or_duplicate_journal_fails_closed(tmp_path):
    report = _report(
        tmp_path,
        "BTCUSDT,long,100,110,95,1\nBTCUSDT,long,100,110,95,1\n",
    )
    assert report["metrics"] is None
    with pytest.raises(ValueError, match="invalid or incomplete"):
        build_trial_evidence("run-1", report)


def test_run_id_and_parent_fingerprint_are_explicitly_validated(tmp_path):
    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    with pytest.raises(ValueError, match="run_id"):
        build_trial_evidence("  ", report)
    with pytest.raises(ValueError, match="parent_evidence_fingerprint"):
        build_trial_evidence("run-1", report, parent_evidence_fingerprint="not-a-digest")


def test_source_artifact_change_changes_evidence_even_when_journal_semantics_match(tmp_path):
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"
    first_path.write_bytes(b"symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,1\n")
    second_path.write_bytes(b"symbol,side,entry,exit,stop_loss,quantity\r\nBTCUSDT,long,100,110,95,1\r\n")
    first_report = build_payload(str(first_path))
    second_report = build_payload(str(second_path))
    assert first_report["journal_fingerprint"] == second_report["journal_fingerprint"]
    assert first_report["source_fingerprint"] != second_report["source_fingerprint"]
    first = build_trial_evidence("run-1", first_report)
    second = build_trial_evidence("run-1", second_report)
    assert first["evidence_fingerprint"] != second["evidence_fingerprint"]


def test_source_fingerprint_tampering_invalidates_evidence(tmp_path):
    evidence = build_trial_evidence("run-1", _report(tmp_path, "BTCUSDT,long,100,110,95,1\n"))
    tampered = deepcopy(evidence)
    tampered["source_fingerprint"] = "0" * 64
    assert not verify_trial_evidence(tampered)


def test_legacy_report_v1_without_source_fingerprint_remains_compatible(tmp_path):
    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    report.pop("source_fingerprint")
    evidence = build_trial_evidence("legacy-run", report)
    assert evidence["source_fingerprint"] is None
    assert verify_trial_evidence(evidence)


def test_present_source_fingerprint_still_fails_closed_when_invalid(tmp_path):
    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    report["source_fingerprint"] = "not-a-digest"
    with pytest.raises(ValueError, match="source_fingerprint"):
        build_trial_evidence("run-1", report)


def test_trial_evidence_validator_rejects_invalid_run_id_and_count(tmp_path):
    from tradeguard.evidence import validate_trial_evidence

    evidence = build_trial_evidence("run-1", _report(tmp_path, "BTCUSDT,long,100,110,95,1\n"))

    broken_run = deepcopy(evidence)
    broken_run["run_id"] = "   "
    assert not validate_trial_evidence({k: v for k, v in broken_run.items() if k != "evidence_fingerprint"})

    broken_count = deepcopy(evidence)
    broken_count["record_count"] = -1
    assert not verify_trial_evidence(broken_count)


def test_trial_evidence_validator_rejects_invalid_parent_and_source_digests(tmp_path):
    evidence = build_trial_evidence("run-1", _report(tmp_path, "BTCUSDT,long,100,110,95,1\n"))

    broken_parent = deepcopy(evidence)
    broken_parent["parent_evidence_fingerprint"] = "x" * 64
    assert not verify_trial_evidence(broken_parent)

    broken_source = deepcopy(evidence)
    broken_source["source_fingerprint"] = "z" * 64
    assert not verify_trial_evidence(broken_source)


def test_trial_evidence_validator_rejects_import_accounting_contradictions(tmp_path):
    source = tmp_path / "mapped.csv"
    source.write_text("ticker,direction,open_px,close_px\nBTCUSDT,long,100,110\n", encoding="utf-8")
    report = build_payload(
        str(source),
        import_mapping={"symbol": "ticker", "side": "direction", "entry": "open_px", "exit": "close_px"},
    )
    evidence = build_trial_evidence("run-1", report)

    broken_rows = deepcopy(evidence)
    broken_rows["import"]["source_rows"] = 2
    assert not verify_trial_evidence(broken_rows)

    broken_complete = deepcopy(evidence)
    broken_complete["import"]["complete"] = False
    assert not verify_trial_evidence(broken_complete)

    broken_source = deepcopy(evidence)
    broken_source["import"]["source_fingerprint"] = "0" * 64
    assert not verify_trial_evidence(broken_source)


def test_trial_evidence_validator_preserves_legacy_null_source_provenance(tmp_path):
    from tradeguard.evidence import validate_trial_evidence

    report = _report(tmp_path, "BTCUSDT,long,100,110,95,1\n")
    report.pop("source_fingerprint")
    evidence = build_trial_evidence("legacy-run", report)
    unsigned = deepcopy(evidence)
    unsigned.pop("evidence_fingerprint")
    assert validate_trial_evidence(unsigned)
    assert verify_trial_evidence(evidence)
