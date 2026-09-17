"""TradeGuard OSS public package."""

from .analytics import JournalMetrics, analyze_trades
from .integrity import DuplicateTrade, find_duplicate_trades, journal_fingerprint
from .models import Trade
from .risk import (
    Exposure,
    InitialRiskAnalysis,
    InitialRiskDiagnostic,
    RiskBreach,
    RiskLimits,
    aggregate_exposure,
    analyze_initial_risk,
    check_risk_limits,
    trade_initial_risk,
    trade_notional,
)
from .validation import ValidationIssue, validate_trades

__all__ = [
    "DuplicateTrade",
    "Exposure",
    "InitialRiskAnalysis",
    "InitialRiskDiagnostic",
    "JournalMetrics",
    "RiskBreach",
    "RiskLimits",
    "Trade",
    "ValidationIssue",
    "aggregate_exposure",
    "analyze_initial_risk",
    "analyze_trades",
    "check_risk_limits",
    "find_duplicate_trades",
    "journal_fingerprint",
    "trade_initial_risk",
    "trade_notional",
    "validate_trades",
]

__version__ = "0.4.0"
