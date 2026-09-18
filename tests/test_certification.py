from copy import deepcopy

from tradeguard.certification import (
    CERTIFICATION_FAIL,
    CERTIFICATION_PASS,
    EVIDENCE_BUNDLE_SCHEMA,
    build_evidence_bundle,
    validate_evidence_bundle,
    verify_evidence_bundle,
)
from tradeguard.cli import build_payload
from tradeguard.evidence import build_trial_evidence


def _evidence(tmp_path, run_id="run-1", parent=None):
    path = tmp_path / "journal.csv"
    path.write_text(
        "symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,1\n",
        encoding="utf-8",
    )
    report = build_payload(str(path))
    return build_trial_evidence(
        run_id,
        report,
        configuration={"stage": "oos"},
        parent_evidence_fingerprint=parent,
    )


def test_bundle_is_deterministic_and_verifiable(tmp_path):
    evidence = _evidence(tmp_path)
    first = build_evidence_bundle(evidence)
    second = build_evidence_bundle(evidence)
    assert first == second
    assert first["evidence_bundle_schema"] == EVIDENCE_BUNDLE_SCHEMA
    assert first["certification"]["status"] == CERTIFICATION_PASS
    assert verify_evidence_bundle(first)


def test_tampered_evidence_fails_closed(tmp_path):
    evidence = _evidence(tmp_path)
    evidence["metrics"]["net_pnl"] = 999999
    bundle = build_evidence_bundle(evidence)
    assert bundle["certification"]["status"] == CERTIFICATION_FAIL
    assert bundle["certification"]["checks"]["trial_evidence_valid"] is False
    assert verify_evidence_bundle(bundle)


def test_parent_chain_mismatch_fails_certification(tmp_path):
    parent = _evidence(tmp_path, run_id="parent")
    child = _evidence(tmp_path, run_id="child", parent=parent["evidence_fingerprint"])
    bundle = build_evidence_bundle(child, expected_parent_fingerprint="0" * 64)
    assert bundle["certification"]["status"] == CERTIFICATION_FAIL
    assert bundle["certification"]["checks"]["parent_link_matches"] is False
    assert verify_evidence_bundle(bundle)


def test_bundle_tampering_invalidates_bundle(tmp_path):
    bundle = build_evidence_bundle(_evidence(tmp_path))
    tampered = deepcopy(bundle)
    tampered["certification"]["status"] = CERTIFICATION_FAIL
    assert not verify_evidence_bundle(tampered)


def test_material_evidence_change_changes_bundle_fingerprint(tmp_path):
    first = build_evidence_bundle(_evidence(tmp_path, run_id="run-1"))
    second = build_evidence_bundle(_evidence(tmp_path, run_id="run-2"))
    assert first["bundle_fingerprint"] != second["bundle_fingerprint"]


def test_bundle_accepts_signed_additive_top_level_member(tmp_path):
    from tradeguard.evidence import _sha256

    bundle = build_evidence_bundle(_evidence(tmp_path))
    bundle["future_optional_member"] = {"version": 1}
    unsigned = deepcopy(bundle)
    unsigned.pop("bundle_fingerprint")
    bundle["bundle_fingerprint"] = _sha256(unsigned)

    assert validate_evidence_bundle(bundle)
    assert verify_evidence_bundle(bundle)


def test_bundle_additive_member_tampering_fails_closed(tmp_path):
    from tradeguard.evidence import _sha256

    bundle = build_evidence_bundle(_evidence(tmp_path))
    bundle["future_optional_member"] = {"version": 1}
    unsigned = deepcopy(bundle)
    unsigned.pop("bundle_fingerprint")
    bundle["bundle_fingerprint"] = _sha256(unsigned)
    assert verify_evidence_bundle(bundle)

    bundle["future_optional_member"]["version"] = 2
    assert not verify_evidence_bundle(bundle)


def test_bundle_validator_rejects_malformed_certification_shape(tmp_path):
    bundle = build_evidence_bundle(_evidence(tmp_path))

    broken_scope = deepcopy(bundle)
    broken_scope["certification"]["scope"] = "other"
    assert not validate_evidence_bundle(broken_scope)

    broken_status = deepcopy(bundle)
    broken_status["certification"]["status"] = "MAYBE"
    assert not validate_evidence_bundle(broken_status)

    broken_checks = deepcopy(bundle)
    broken_checks["certification"]["checks"]["future_check"] = True
    assert not validate_evidence_bundle(broken_checks)


def test_bundle_validator_rejects_invalid_expected_parent_digest(tmp_path):
    bundle = build_evidence_bundle(_evidence(tmp_path))
    bundle["expected_parent_fingerprint"] = "not-a-digest"
    assert not validate_evidence_bundle(bundle)
