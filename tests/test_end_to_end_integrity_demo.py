from pathlib import Path

import pytest

from tradeguard.certification import verify_evidence_bundle
from tradeguard.cli import _reconciliation_payload, build_payload
from tradeguard.evidence import build_trial_evidence
from tradeguard.reconciliation_evidence import verify_reconciliation_evidence


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "examples" / "integrity_reference.csv"
CANDIDATE = ROOT / "examples" / "integrity_candidate.csv"


def test_integrity_demo_reference_analyzes_successfully():
    report = build_payload(str(REFERENCE))
    assert report["metrics"] is not None
    assert report["metrics"]["trades"] == 2
    assert len(report["source_fingerprint"]) == 64
    assert len(report["journal_fingerprint"]) == 64


def test_integrity_demo_reconciliation_detects_drift():
    payload = _reconciliation_payload(str(REFERENCE), str(CANDIDATE))
    assert payload["clean"] is False
    assert payload["modified_rows"] == 1
    assert payload["mismatches"]
    assert verify_reconciliation_evidence(payload)


def test_integrity_demo_evidence_and_certification_verify():
    from tradeguard.certification import build_evidence_bundle

    report = build_payload(str(REFERENCE))
    evidence = build_trial_evidence("demo-oos-001", report)
    bundle = build_evidence_bundle(evidence)
    assert bundle["certification"]["status"] == "PASS"
    assert verify_evidence_bundle(bundle)
