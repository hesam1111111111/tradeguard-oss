from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .integrity import find_duplicate_trades, journal_fingerprint
from .models import Trade
from .validation import ValidationIssue, validate_trades


@dataclass(frozen=True, slots=True)
class JournalDiagnostics:
    fingerprint: str
    trade_count: int
    error_count: int
    warning_count: int
    duplicate_count: int
    valid_for_metrics: bool
    validation_issues: tuple[ValidationIssue, ...]
    duplicate_trades: tuple[dict[str, int], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "fingerprint": self.fingerprint,
            "trade_count": self.trade_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "duplicate_count": self.duplicate_count,
            "valid_for_metrics": self.valid_for_metrics,
            "validation_issues": [asdict(issue) for issue in self.validation_issues],
            "duplicate_trades": list(self.duplicate_trades),
        }


def diagnose_journal(trades: Iterable[Trade]) -> JournalDiagnostics:
    """Produce deterministic, machine-readable journal diagnostics.

    Exact duplicates are treated as errors because silently including them can
    inflate metrics. Validation warnings do not suppress metrics by themselves.
    """
    materialized = list(trades)
    issues = tuple(validate_trades(materialized))
    duplicates = tuple(
        {"first_index": duplicate.first_index, "duplicate_index": duplicate.duplicate_index}
        for duplicate in find_duplicate_trades(materialized)
    )
    error_count = sum(issue.severity == "error" for issue in issues)
    warning_count = sum(issue.severity == "warning" for issue in issues)
    duplicate_count = len(duplicates)
    return JournalDiagnostics(
        fingerprint=journal_fingerprint(materialized),
        trade_count=len(materialized),
        error_count=error_count,
        warning_count=warning_count,
        duplicate_count=duplicate_count,
        valid_for_metrics=(error_count == 0 and duplicate_count == 0),
        validation_issues=issues,
        duplicate_trades=duplicates,
    )
