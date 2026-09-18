import json
from copy import deepcopy
from pathlib import Path

from tradeguard.certification import build_evidence_bundle, verify_evidence_bundle
from tradeguard.cli import _reconciliation_payload, build_payload
from tradeguard.evidence import build_trial_evidence, verify_trial_evidence
from tradeguard.reconciliation_evidence import verify_reconciliation_evidence

_RECONCILIATION_REQUIRED = {
    "reconciliation_schema": str,
    "reference": str,
    "candidate": str,
    "reference_source_fingerprint": str,
    "candidate_source_fingerprint": str,
    "clean": bool,
    "reference_fingerprint": str,
    "candidate_fingerprint": str,
    "reference_rows": int,
    "candidate_rows": int,
    "exact_matches": int,
    "modified_rows": int,
    "missing": list,
    "unexpected": list,
    "mismatches": list,
    "reconciliation_evidence_fingerprint": str,
}

_TRIAL_REQUIRED = {
    "trial_ledger_schema": str,
    "run_id": str,
    "parent_evidence_fingerprint": (str, type(None)),
    "source_fingerprint": (str, type(None)),
    "journal_fingerprint": str,
    "record_count": int,
    "configuration": dict,
    "import": (dict, type(None)),
    "metrics": dict,
    "diagnostics": dict,
    "risk": (dict, type(None)),
    "segments": (dict, type(None)),
    "evidence_fingerprint": str,
}

_BUNDLE_REQUIRED = {
    "evidence_bundle_schema": str,
    "certification": dict,
    "expected_parent_fingerprint": (str, type(None)),
    "evidence": dict,
    "bundle_fingerprint": str,
}


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _journal(tmp_path: Path, name: str, rows: str) -> Path:
    path = tmp_path / name
    path.write_text("symbol,side,entry,exit,stop_loss,quantity\n" + rows, encoding="utf-8")
    return path


def _reconciliation(tmp_path: Path) -> dict:
    reference = _journal(tmp_path, "reference.csv", "BTCUSDT,long,100,110,95,1\n")
    candidate = _journal(tmp_path, "candidate.csv", "BTCUSDT,long,100,109,95,1\n")
    payload = _reconciliation_payload(str(reference), str(candidate))
    payload["reference"] = "reference.csv"
    payload["candidate"] = "candidate.csv"
    return payload


def _trial(tmp_path: Path) -> dict:
    journal = _journal(tmp_path, "trial.csv", "BTCUSDT,long,100,110,95,1\n")
    report = build_payload(str(journal))
    report["source"] = "trial.csv"
    return build_trial_evidence("consumer-run", report, configuration={"stage": "oos"})


def _bundle(tmp_path: Path) -> dict:
    return build_evidence_bundle(_trial(tmp_path))


def test_reconciliation_v1_established_top_level_contract(tmp_path: Path):
    payload = _reconciliation(tmp_path)
    assert payload["reconciliation_schema"] == "tradeguard.reconciliation.v1"
    for name, expected_type in _RECONCILIATION_REQUIRED.items():
        assert name in payload
        assert isinstance(payload[name], expected_type)
    assert verify_reconciliation_evidence(payload)


def test_trial_ledger_v1_established_top_level_contract(tmp_path: Path):
    evidence = _trial(tmp_path)
    assert evidence["trial_ledger_schema"] == "tradeguard.trial-ledger.v1"
    for name, expected_type in _TRIAL_REQUIRED.items():
        assert name in evidence
        assert isinstance(evidence[name], expected_type)
    assert verify_trial_evidence(evidence)


def test_evidence_bundle_v1_established_top_level_contract(tmp_path: Path):
    bundle = _bundle(tmp_path)
    assert bundle["evidence_bundle_schema"] == "tradeguard.evidence-bundle.v1"
    for name, expected_type in _BUNDLE_REQUIRED.items():
        assert name in bundle
        assert isinstance(bundle[name], expected_type)
    assert bundle["certification"]["status"] == "PASS"
    assert verify_evidence_bundle(bundle)


def test_evidence_contract_serialization_is_deterministic(tmp_path: Path):
    first_reconciliation = _reconciliation(tmp_path)
    second_reconciliation = _reconciliation(tmp_path)
    assert _canonical_bytes(first_reconciliation) == _canonical_bytes(second_reconciliation)

    first_trial = _trial(tmp_path)
    second_trial = _trial(tmp_path)
    assert _canonical_bytes(first_trial) == _canonical_bytes(second_trial)

    first_bundle = _bundle(tmp_path)
    second_bundle = _bundle(tmp_path)
    assert _canonical_bytes(first_bundle) == _canonical_bytes(second_bundle)


def test_consumers_can_ignore_additive_unknown_members(tmp_path: Path):
    fixtures = [
        (_reconciliation(tmp_path), _RECONCILIATION_REQUIRED),
        (_trial(tmp_path), _TRIAL_REQUIRED),
        (_bundle(tmp_path), _BUNDLE_REQUIRED),
    ]
    for payload, required in fixtures:
        established = {name: deepcopy(payload[name]) for name in required}
        payload["future_optional_member"] = {"ignored_by_v1_consumer": True}
        consumed = {name: payload[name] for name in required}
        assert consumed == established


def test_trial_ledger_legacy_null_source_provenance_remains_consumer_compatible(tmp_path: Path):
    journal = _journal(tmp_path, "legacy.csv", "BTCUSDT,long,100,110,95,1\n")
    report = build_payload(str(journal))
    report.pop("source_fingerprint")
    evidence = build_trial_evidence("legacy-consumer-run", report)
    assert evidence["source_fingerprint"] is None
    assert verify_trial_evidence(evidence)
