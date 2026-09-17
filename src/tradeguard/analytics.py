from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Trade


@dataclass(frozen=True, slots=True)
class JournalMetrics:
    trades: int
    wins: int
    losses: int
    breakeven: int
    win_rate: float
    net_pnl: float
    gross_profit: float
    gross_loss: float
    profit_factor: float | None
    expectancy: float
    max_drawdown: float
    average_r_multiple: float | None
    best_trade: float | None
    worst_trade: float | None


@dataclass(frozen=True, slots=True)
class JournalSegment:
    key: str
    metrics: JournalMetrics


def _max_drawdown(pnls: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def analyze_trades(trades: Iterable[Trade]) -> JournalMetrics:
    items = list(trades)
    pnls = [t.pnl for t in items]
    wins = sum(1 for pnl in pnls if pnl > 0)
    losses = sum(1 for pnl in pnls if pnl < 0)
    breakeven = sum(1 for pnl in pnls if pnl == 0)
    total = len(items)
    gross_profit = sum(pnl for pnl in pnls if pnl > 0)
    gross_loss = abs(sum(pnl for pnl in pnls if pnl < 0))
    r_values = [r for t in items if (r := t.r_multiple) is not None]

    return JournalMetrics(
        trades=total,
        wins=wins,
        losses=losses,
        breakeven=breakeven,
        win_rate=(wins / total) if total else 0.0,
        net_pnl=sum(pnls),
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=(gross_profit / gross_loss) if gross_loss else None,
        expectancy=(sum(pnls) / total) if total else 0.0,
        max_drawdown=_max_drawdown(pnls),
        average_r_multiple=(sum(r_values) / len(r_values)) if r_values else None,
        best_trade=max(pnls) if pnls else None,
        worst_trade=min(pnls) if pnls else None,
    )


def analyze_by_symbol(trades: Iterable[Trade]) -> tuple[JournalSegment, ...]:
    """Return metrics grouped by normalized symbol in deterministic key order."""
    groups: dict[str, list[Trade]] = {}
    for trade in trades:
        symbol = trade.symbol.strip().upper()
        if not symbol:
            raise ValueError("trade.symbol must not be empty")
        groups.setdefault(symbol, []).append(trade)
    return tuple(JournalSegment(key, analyze_trades(groups[key])) for key in sorted(groups))


def analyze_by_side(trades: Iterable[Trade]) -> tuple[JournalSegment, ...]:
    """Return metrics grouped by normalized long/short side in deterministic key order."""
    groups: dict[str, list[Trade]] = {}
    for trade in trades:
        side = trade.normalized_side
        groups.setdefault(side, []).append(trade)
    return tuple(JournalSegment(key, analyze_trades(groups[key])) for key in sorted(groups))
