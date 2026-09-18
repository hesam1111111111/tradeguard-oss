from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from .evidence import _sha256

RECONCILIATION_SCHEMA = "tradeguard.reconciliation.v1"
RECONCILIATION_EVIDENCE_FINGERPRINT = "reconciliation_evidence_fingerprint"
_DIGEST_FIELDS = (
    "reference_source_fingerprint",
    "candidate_source_fingerprint",
    "reference_fingerprint",
    "candidate_fingerprint",
)
_COUNT_FIELDS = (
    "reference_rows",
    "candidate_rows",
    "exact_matches",
    "modified_rows",
)


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _validate_delta_list(value: Any) -> tuple[bool, int]:
    if not isinstance(value, list):
        return False, 0
    total = 0
    for item in value:
        if not isinstance(item, dict):
            return False, 0
        if not isinstance(item.get("record"), dict):
            return False, 0
        count = item.get("count")
        if not _is_non_negative_int(count) or count == 0:
            return False, 0
        total += count
    return True, total


def _validate_mismatches(value: Any) -> tuple[bool, int]:
    if not isinstance(value, list):
        return False, 0
    identities: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            return False, 0
        identity = item.get("identity")
        field = item.get("field")
        if not isinstance(identity, dict):
            return False, 0
        if not isinstance(field, str) or not field.strip():
            return False, 0
        if "reference_value" not in item or "candidate_value" not in item:
            return False, 0
        try:
            identities.add(json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError):
            return False, 0
    return True, len(identities)


def validate_reconciliation_evidence(payload: dict[str, Any]) -> bool:
    """Validate reconciliation v1 structure and internal accounting invariants."""
    if not isinstance(payload, dict):
        return False
    if payload.get("reconciliation_schema") != RECONCILIATION_SCHEMA:
        return False
    if not isinstance(payload.get("reference"), str) or not payload["reference"]:
        return False
    if not isinstance(payload.get("candidate"), str) or not payload["candidate"]:
        return False
    if not isinstance(payload.get("clean"), bool):
        return False
    if any(not _is_sha256(payload.get(name)) for name in _DIGEST_FIELDS):
        return False
    if any(not _is_non_negative_int(payload.get(name)) for name in _COUNT_FIELDS):
        return False

    missing_ok, missing_count = _validate_delta_list(payload.get("missing"))
    unexpected_ok, unexpected_count = _validate_delta_list(payload.get("unexpected"))
    mismatches_ok, modified_identities = _validate_mismatches(payload.get("mismatches"))
    if not (missing_ok and unexpected_ok and mismatches_ok):
        return False

    has_drift = bool(payload["missing"] or payload["unexpected"] or payload["mismatches"])
    if payload["clean"] == has_drift:
        return False
    if payload["modified_rows"] != modified_identities:
        return False
    if payload["reference_rows"] != payload["exact_matches"] + payload["modified_rows"] + missing_count:
        return False
    if payload["candidate_rows"] != payload["exact_matches"] + payload["modified_rows"] + unexpected_count:
        return False
    return True


def sign_reconciliation_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic reconciliation envelope with an integrity fingerprint."""
    unsigned = deepcopy(payload)
    unsigned.pop(RECONCILIATION_EVIDENCE_FINGERPRINT, None)
    if not validate_reconciliation_evidence(unsigned):
        raise ValueError("reconciliation evidence violates tradeguard.reconciliation.v1 contract")
    unsigned[RECONCILIATION_EVIDENCE_FINGERPRINT] = _sha256(unsigned)
    return unsigned


def verify_reconciliation_evidence(payload: dict[str, Any]) -> bool:
    """Fail closed unless both the reconciliation contract and fingerprint verify."""
    if not isinstance(payload, dict):
        return False
    stored = payload.get(RECONCILIATION_EVIDENCE_FINGERPRINT)
    if not _is_sha256(stored):
        return False
    unsigned = deepcopy(payload)
    unsigned.pop(RECONCILIATION_EVIDENCE_FINGERPRINT, None)
    if not validate_reconciliation_evidence(unsigned):
        return False
    try:
        return _sha256(unsigned) == stored
    except (TypeError, ValueError):
        return False
