from __future__ import annotations

from copy import deepcopy
from typing import Any

from .evidence import _sha256

RECONCILIATION_SCHEMA = "tradeguard.reconciliation.v1"
RECONCILIATION_EVIDENCE_FINGERPRINT = "reconciliation_evidence_fingerprint"


def sign_reconciliation_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic reconciliation envelope with an integrity fingerprint."""
    if payload.get("reconciliation_schema") != RECONCILIATION_SCHEMA:
        raise ValueError("reconciliation evidence requires tradeguard.reconciliation.v1")
    signed = deepcopy(payload)
    signed.pop(RECONCILIATION_EVIDENCE_FINGERPRINT, None)
    signed[RECONCILIATION_EVIDENCE_FINGERPRINT] = _sha256(signed)
    return signed


def verify_reconciliation_evidence(payload: dict[str, Any]) -> bool:
    """Fail closed unless the reconciliation envelope fingerprint verifies."""
    if payload.get("reconciliation_schema") != RECONCILIATION_SCHEMA:
        return False
    stored = payload.get(RECONCILIATION_EVIDENCE_FINGERPRINT)
    if not isinstance(stored, str) or len(stored) != 64:
        return False
    unsigned = deepcopy(payload)
    unsigned.pop(RECONCILIATION_EVIDENCE_FINGERPRINT, None)
    try:
        return _sha256(unsigned) == stored
    except (TypeError, ValueError):
        return False
