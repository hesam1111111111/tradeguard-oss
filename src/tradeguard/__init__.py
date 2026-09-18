"""TradeGuard OSS public package."""

from .analytics import (
    JournalMetrics,
    JournalSegment,
    TemporalAnalysis,
    TemporalDiagnostic,
    analyze_by_closed_period,
    analyze_by_side,
    analyze_by_symbol,
    analyze_trades,
)
from .importers import ImportDiagnostic, ImportResult, import_mapped_csv
from .integrity import DuplicateTrade, find_duplicate_trades, journal_fingerprint
from .models import Trade
from .reconciliation import FieldMismatch, ReconciliationResult, RecordDelta, reconcile_journals, reconciliation_fingerprint
from .risk import (
    Exposure,
    InitialRiskAnalysis,
    InitialRiskDiagnostic,
    RiskBreach,
    RiskBudget,
    RiskBudgetBreach,
    RiskBudgetEvaluation,
    RiskLimits,
    aggregate_exposure,
    analyze_initial_risk,
    check_risk_limits,
    evaluate_risk_budget,
    trade_initial_risk,
    trade_notional,
)
from .validation import ValidationIssue, validate_trades

__all__ = [
    "DuplicateTrade",
    "Exposure",
    "ImportDiagnostic",
    "ImportResult",
    "InitialRiskAnalysis",
    "InitialRiskDiagnostic",
    "JournalMetrics",
    "JournalSegment",
    "FieldMismatch",
    "ReconciliationResult",
    "RecordDelta",
    "RiskBreach",
    "RiskBudget",
    "RiskBudgetBreach",
    "RiskBudgetEvaluation",
    "RiskLimits",
    "TemporalAnalysis",
    "TemporalDiagnostic",
    "Trade",
    "ValidationIssue",
    "aggregate_exposure",
    "analyze_by_closed_period",
    "analyze_by_side",
    "analyze_by_symbol",
    "analyze_initial_risk",
    "analyze_trades",
    "check_risk_limits",
    "evaluate_risk_budget",
    "find_duplicate_trades",
    "import_mapped_csv",
    "journal_fingerprint",
    "reconcile_journals",
    "reconciliation_fingerprint",
    "trade_initial_risk",
    "trade_notional",
    "validate_trades",
]

__version__ = "0.7.1"
