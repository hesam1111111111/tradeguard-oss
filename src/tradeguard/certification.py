from __future__ import annotations

from copy import deepcopy
from typing import Any

from .evidence import _sha256, verify_trial_evidence

EVIDENCE_BUNDLE_SCHEMA = "tradeguard.evidence-bundle.v1"
CERTIFICATION_PASS = "PASS"
CERTIFICATION_FAIL = "FAIL"


def build_evidence_bundle(
    evidence: dict[str, Any],
    *,
    expected_parent_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic offline verification result for Trial Ledger evidence.

    PASS certifies only the internal integrity checks declared here. It does not
    attest broker provenance, execution, profitability, identity, or safety.
    """
    checks = {
        "trial_evidence_valid": verify_trial_evidence(
            evidence,
            expected_parent_fingerprint=expected_parent_fingerprint,
        ),
    }
    if expected_parent_fingerprint is not None:
        checks["parent_link_matches"] = (
            evidence.get("parent_evidence_fingerprint") == expected_parent_fingerprint
        )

    status = CERTIFICATION_PASS if all(checks.values()) else CERTIFICATION_FAIL
    bundle: dict[str, Any] = {
        "evidence_bundle_schema": EVIDENCE_BUNDLE_SCHEMA,
        "certification": {
            "status": status,
            "checks": checks,
            "scope": "internal-evidence-integrity",
        },
        "expected_parent_fingerprint": expected_parent_fingerprint,
        "evidence": deepcopy(evidence),
    }
    bundle["bundle_fingerprint"] = _sha256(bundle)
    return bundle


def verify_evidence_bundle(bundle: dict[str, Any]) -> bool:
    """Verify bundle integrity and re-run its deterministic certification checks."""
    if bundle.get("evidence_bundle_schema") != EVIDENCE_BUNDLE_SCHEMA:
        return False
    stored = bundle.get("bundle_fingerprint")
    if not isinstance(stored, str):
        return False

    unsigned = deepcopy(bundle)
    unsigned.pop("bundle_fingerprint", None)
    try:
        if _sha256(unsigned) != stored:
            return False
    except (TypeError, ValueError):
        return False

    evidence = bundle.get("evidence")
    certification = bundle.get("certification")
    if not isinstance(evidence, dict) or not isinstance(certification, dict):
        return False

    rebuilt = build_evidence_bundle(
        evidence,
        expected_parent_fingerprint=bundle.get("expected_parent_fingerprint"),
    )
    return (
        rebuilt["certification"] == certification
        and rebuilt["bundle_fingerprint"] == stored
    )
