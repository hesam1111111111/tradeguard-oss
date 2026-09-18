"""TradeGuard OSS public package."""

from .adapters import IMPORT_PROFILES, available_import_profiles, get_import_profile, import_csv_with_profile
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
from .certification import (
    CERTIFICATION_FAIL,
    CERTIFICATION_PASS,
    EVIDENCE_BUNDLE_SCHEMA,
    build_evidence_bundle,
    verify_evidence_bundle,
)
from .evidence import TRIAL_LEDGER_SCHEMA, build_trial_evidence, validate_trial_evidence, verify_trial_evidence
from .importers import ImportDiagnostic, ImportResult, import_mapped_csv
from .integrity import DuplicateTrade, find_duplicate_trades, journal_fingerprint
from .models import Trade
from .reconciliation import FieldMismatch, ReconciliationResult, RecordDelta, reconcile_journals, reconciliation_fingerprint
from .reconciliation_evidence import sign_reconciliation_evidence, validate_reconciliation_evidence, verify_reconciliation_evidence
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
    "CERTIFICATION_FAIL",
    "CERTIFICATION_PASS",
    "EVIDENCE_BUNDLE_SCHEMA",
    "DuplicateTrade",
    "Exposure",
    "IMPORT_PROFILES",
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
    "TRIAL_LEDGER_SCHEMA",
    "TemporalAnalysis",
    "TemporalDiagnostic",
    "Trade",
    "ValidationIssue",
    "aggregate_exposure",
    "available_import_profiles",
    "analyze_by_closed_period",
    "analyze_by_side",
    "analyze_by_symbol",
    "analyze_initial_risk",
    "analyze_trades",
    "build_evidence_bundle",
    "build_trial_evidence",
    "check_risk_limits",
    "evaluate_risk_budget",
    "find_duplicate_trades",
    "get_import_profile",
    "import_csv_with_profile",
    "import_mapped_csv",
    "journal_fingerprint",
    "reconcile_journals",
    "reconciliation_fingerprint",
    "sign_reconciliation_evidence",
    "trade_initial_risk",
    "trade_notional",
    "validate_reconciliation_evidence",
    "validate_trial_evidence",
    "validate_trades",
    "verify_evidence_bundle",
    "verify_reconciliation_evidence",
    "verify_trial_evidence",
]

__version__ = "0.15.0"
