"""TradeGuard OSS public package."""

from .analytics import JournalMetrics, analyze_trades
from .integrity import DuplicateTrade, find_duplicate_trades, journal_fingerprint
from .models import Trade
from .validation import ValidationIssue, validate_trades

__all__ = [
    "DuplicateTrade",
    "JournalMetrics",
    "Trade",
    "ValidationIssue",
    "analyze_trades",
    "find_duplicate_trades",
    "journal_fingerprint",
    "validate_trades",
]

__version__ = "0.2.0"
