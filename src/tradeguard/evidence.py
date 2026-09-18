from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

TRIAL_LEDGER_SCHEMA = "tradeguard.trial-ledger.v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _validate_fingerprint(value: str, name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest") from exc


def build_trial_evidence(
    run_id: str,
    report: dict[str, Any],
    *,
    configuration: dict[str, Any] | None = None,
    parent_evidence_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, local evidence record from a valid TradeGuard report.

    Timestamps are intentionally excluded: identical semantic inputs must produce
    identical evidence. The caller supplies run_id because TradeGuard must not
    invent experiment provenance.
    """
    run_id = run_id.strip()
    if not run_id:
        raise ValueError("run_id must be non-blank")
    if report.get("report_schema") != "tradeguard.report.v1":
        raise ValueError("trial evidence requires tradeguard.report.v1")
    source_fingerprint = report.get("source_fingerprint")
    if not isinstance(source_fingerprint, str):
        raise ValueError("report is missing source_fingerprint")
    _validate_fingerprint(source_fingerprint, "source_fingerprint")
    fingerprint = report.get("journal_fingerprint")
    if not isinstance(fingerprint, str):
        raise ValueError("report is missing journal_fingerprint")
    _validate_fingerprint(fingerprint, "journal_fingerprint")
    if report.get("metrics") is None:
        raise ValueError("cannot produce trial evidence from an invalid or incomplete journal")

    if parent_evidence_fingerprint is not None:
        _validate_fingerprint(parent_evidence_fingerprint, "parent_evidence_fingerprint")

    imported = report.get("import")
    import_evidence = None
    if imported is not None:
        import_evidence = {
            "mode": imported.get("mode"),
            "source_fingerprint": source_fingerprint,
            "complete": imported.get("complete"),
            "source_rows": imported.get("source_rows"),
            "imported_rows": imported.get("imported_rows"),
            "rejected_rows": imported.get("rejected_rows"),
            "mapping": deepcopy(imported.get("mapping")),
            "diagnostics": deepcopy(imported.get("diagnostics")),
        }

    record: dict[str, Any] = {
        "trial_ledger_schema": TRIAL_LEDGER_SCHEMA,
        "run_id": run_id,
        "parent_evidence_fingerprint": parent_evidence_fingerprint,
        "source_fingerprint": source_fingerprint,
        "journal_fingerprint": fingerprint,
        "record_count": report["metrics"].get("trades"),
        "configuration": deepcopy(configuration or {}),
        "import": import_evidence,
        "metrics": deepcopy(report.get("metrics")),
        "diagnostics": deepcopy(report.get("diagnostics")),
        "risk": deepcopy(report.get("risk")),
        "segments": deepcopy(report.get("segments")),
    }
    record["evidence_fingerprint"] = _sha256(record)
    return record


def verify_trial_evidence(
    evidence: dict[str, Any],
    *,
    expected_parent_fingerprint: str | None = None,
) -> bool:
    """Return True only when the evidence fingerprint and optional chain link match."""
    if evidence.get("trial_ledger_schema") != TRIAL_LEDGER_SCHEMA:
        return False
    stored = evidence.get("evidence_fingerprint")
    if not isinstance(stored, str):
        return False
    if expected_parent_fingerprint is not None and evidence.get("parent_evidence_fingerprint") != expected_parent_fingerprint:
        return False
    unsigned = deepcopy(evidence)
    unsigned.pop("evidence_fingerprint", None)
    try:
        return _sha256(unsigned) == stored
    except (TypeError, ValueError):
        return False
