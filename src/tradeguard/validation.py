from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Trade


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    index: int
    code: str
    message: str
    severity: str = "error"


def validate_trades(trades: Iterable[Trade]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for index, trade in enumerate(trades):
        side = trade.side.strip().lower()
        if not trade.symbol.strip():
            issues.append(ValidationIssue(index, "missing_symbol", "Trade symbol is required."))
        if side not in {"long", "short"}:
            issues.append(ValidationIssue(index, "invalid_side", "Side must be 'long' or 'short'."))
        if trade.entry <= 0 or trade.exit <= 0:
            issues.append(ValidationIssue(index, "invalid_price", "Entry and exit must be positive."))
        if trade.quantity <= 0:
            issues.append(ValidationIssue(index, "invalid_quantity", "Quantity must be positive."))
        if trade.stop_loss is None:
            issues.append(ValidationIssue(index, "missing_stop_loss", "Stop loss is missing.", "warning"))
        elif side == "long" and trade.stop_loss >= trade.entry:
            issues.append(ValidationIssue(index, "invalid_stop_loss", "Long stop loss must be below entry."))
        elif side == "short" and trade.stop_loss <= trade.entry:
            issues.append(ValidationIssue(index, "invalid_stop_loss", "Short stop loss must be above entry."))
        if trade.opened_at and trade.closed_at and trade.closed_at < trade.opened_at:
            issues.append(ValidationIssue(index, "invalid_time_order", "Closed time cannot precede opened time."))
    return issues
