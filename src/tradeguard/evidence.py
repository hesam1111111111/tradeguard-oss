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


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_trial_evidence(evidence: dict[str, Any]) -> bool:
    """Validate Trial Ledger v1 structure and internal provenance/accounting invariants."""
    if not isinstance(evidence, dict):
        return False
    if evidence.get("trial_ledger_schema") != TRIAL_LEDGER_SCHEMA:
        return False

    run_id = evidence.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        return False

    parent = evidence.get("parent_evidence_fingerprint")
    if parent is not None and not _is_sha256(parent):
        return False

    source_fingerprint = evidence.get("source_fingerprint")
    if source_fingerprint is not None and not _is_sha256(source_fingerprint):
        return False

    if not _is_sha256(evidence.get("journal_fingerprint")):
        return False

    record_count = evidence.get("record_count")
    if not _is_non_negative_int(record_count):
        return False

    if not isinstance(evidence.get("configuration"), dict):
        return False

    metrics = evidence.get("metrics")
    if not isinstance(metrics, dict):
        return False
    if metrics.get("trades") != record_count:
        return False

    diagnostics = evidence.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return False

    risk = evidence.get("risk")
    if risk is not None and not isinstance(risk, dict):
        return False

    segments = evidence.get("segments")
    if segments is not None and not isinstance(segments, dict):
        return False

    imported = evidence.get("import")
    if imported is not None:
        if not isinstance(imported, dict):
            return False
        if not isinstance(imported.get("mode"), str) or not imported["mode"].strip():
            return False
        if imported.get("source_fingerprint") != source_fingerprint:
            return False
        if not isinstance(imported.get("complete"), bool):
            return False

        source_rows = imported.get("source_rows")
        imported_rows = imported.get("imported_rows")
        rejected_rows = imported.get("rejected_rows")
        if not all(_is_non_negative_int(value) for value in (source_rows, imported_rows, rejected_rows)):
            return False
        if source_rows != imported_rows + rejected_rows:
            return False
        if imported["complete"] != (rejected_rows == 0):
            return False
        if not isinstance(imported.get("mapping"), dict):
            return False
        if not isinstance(imported.get("diagnostics"), list):
            return False

    return True


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
    if source_fingerprint is not None:
        if not isinstance(source_fingerprint, str):
            raise ValueError("source_fingerprint must be a 64-character SHA-256 hex digest")
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
    if not validate_trial_evidence(record):
        raise ValueError("trial evidence violates tradeguard.trial-ledger.v1 contract")
    record["evidence_fingerprint"] = _sha256(record)
    return record


def verify_trial_evidence(
    evidence: dict[str, Any],
    *,
    expected_parent_fingerprint: str | None = None,
) -> bool:
    """Return True only when the Trial Ledger contract, fingerprint, and optional chain link match."""
    if not isinstance(evidence, dict):
        return False
    stored = evidence.get("evidence_fingerprint")
    if not _is_sha256(stored):
        return False
    if expected_parent_fingerprint is not None:
        if not _is_sha256(expected_parent_fingerprint):
            return False
        if evidence.get("parent_evidence_fingerprint") != expected_parent_fingerprint:
            return False
    unsigned = deepcopy(evidence)
    unsigned.pop("evidence_fingerprint", None)
    if not validate_trial_evidence(unsigned):
        return False
    try:
        return _sha256(unsigned) == stored
    except (TypeError, ValueError):
        return False
