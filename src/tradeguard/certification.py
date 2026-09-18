from __future__ import annotations

from copy import deepcopy
from typing import Any

from .evidence import _sha256, verify_trial_evidence

EVIDENCE_BUNDLE_SCHEMA = "tradeguard.evidence-bundle.v1"
CERTIFICATION_PASS = "PASS"
CERTIFICATION_FAIL = "FAIL"
_CERTIFICATION_SCOPE = "internal-evidence-integrity"


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _expected_certification(
    evidence: dict[str, Any],
    expected_parent_fingerprint: str | None,
) -> dict[str, Any]:
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
    return {
        "status": CERTIFICATION_PASS if all(checks.values()) else CERTIFICATION_FAIL,
        "checks": checks,
        "scope": _CERTIFICATION_SCOPE,
    }


def validate_evidence_bundle(bundle: dict[str, Any]) -> bool:
    """Validate established Evidence Bundle v1 structure and certification semantics."""
    if not isinstance(bundle, dict):
        return False
    if bundle.get("evidence_bundle_schema") != EVIDENCE_BUNDLE_SCHEMA:
        return False

    stored = bundle.get("bundle_fingerprint")
    if not _is_sha256(stored):
        return False

    expected_parent = bundle.get("expected_parent_fingerprint")
    if expected_parent is not None and not _is_sha256(expected_parent):
        return False

    evidence = bundle.get("evidence")
    certification = bundle.get("certification")
    if not isinstance(evidence, dict) or not isinstance(certification, dict):
        return False

    status = certification.get("status")
    checks = certification.get("checks")
    scope = certification.get("scope")
    if status not in (CERTIFICATION_PASS, CERTIFICATION_FAIL):
        return False
    if not isinstance(checks, dict) or scope != _CERTIFICATION_SCOPE:
        return False

    expected = _expected_certification(evidence, expected_parent)
    expected_checks = expected["checks"]
    if set(checks) != set(expected_checks):
        return False
    if any(checks[name] is not expected_checks[name] for name in expected_checks):
        return False

    return status == expected["status"]


def build_evidence_bundle(
    evidence: dict[str, Any],
    *,
    expected_parent_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic offline verification result for Trial Ledger evidence.

    PASS certifies only the internal integrity checks declared here. It does not
    attest broker provenance, execution, profitability, identity, or safety.
    """
    certification = _expected_certification(evidence, expected_parent_fingerprint)
    bundle: dict[str, Any] = {
        "evidence_bundle_schema": EVIDENCE_BUNDLE_SCHEMA,
        "certification": certification,
        "expected_parent_fingerprint": expected_parent_fingerprint,
        "evidence": deepcopy(evidence),
    }
    bundle["bundle_fingerprint"] = _sha256(bundle)
    return bundle


def verify_evidence_bundle(bundle: dict[str, Any]) -> bool:
    """Verify bundle integrity plus established Evidence Bundle v1 semantics."""
    if not validate_evidence_bundle(bundle):
        return False

    stored = bundle["bundle_fingerprint"]
    unsigned = deepcopy(bundle)
    unsigned.pop("bundle_fingerprint", None)
    try:
        return _sha256(unsigned) == stored
    except (TypeError, ValueError):
        return False
