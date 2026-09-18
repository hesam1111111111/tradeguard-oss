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
