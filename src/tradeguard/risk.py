from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Trade


@dataclass(frozen=True, slots=True)
class Exposure:
    symbol: str
    long_notional: float
    short_notional: float

    @property
    def gross_notional(self) -> float:
        return self.long_notional + self.short_notional

    @property
    def net_notional(self) -> float:
        return self.long_notional - self.short_notional


@dataclass(frozen=True, slots=True)
class RiskLimits:
    max_gross_notional: float | None = None
    max_symbol_gross_notional: float | None = None
    max_trade_notional: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("max_gross_notional", self.max_gross_notional),
            ("max_symbol_gross_notional", self.max_symbol_gross_notional),
            ("max_trade_notional", self.max_trade_notional),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class RiskBreach:
    code: str
    message: str
    actual: float
    limit: float
    symbol: str | None = None
    trade_index: int | None = None


def trade_notional(trade: Trade) -> float:
    """Return absolute entry notional for a trade."""
    return abs(trade.entry * trade.quantity)


def aggregate_exposure(trades: Iterable[Trade]) -> tuple[Exposure, ...]:
    """Aggregate entry notional by normalized symbol and side.

    This is deliberately price-at-entry exposure, not live mark-to-market exposure.
    """
    totals: dict[str, list[float]] = {}
    for trade in trades:
        symbol = trade.symbol.strip().upper()
        long_short = totals.setdefault(symbol, [0.0, 0.0])
        notional = trade_notional(trade)
        if trade.normalized_side == "long":
            long_short[0] += notional
        else:
            long_short[1] += notional

    return tuple(
        Exposure(symbol=symbol, long_notional=values[0], short_notional=values[1])
        for symbol, values in sorted(totals.items())
    )


def check_risk_limits(trades: Iterable[Trade], limits: RiskLimits) -> tuple[RiskBreach, ...]:
    """Evaluate deterministic notional limits without executing or modifying trades."""
    trade_list = tuple(trades)
    breaches: list[RiskBreach] = []

    if limits.max_trade_notional is not None:
        for index, trade in enumerate(trade_list):
            actual = trade_notional(trade)
            if actual > limits.max_trade_notional:
                breaches.append(
                    RiskBreach(
                        code="max_trade_notional",
                        message=f"Trade {index} exceeds maximum trade notional.",
                        actual=actual,
                        limit=limits.max_trade_notional,
                        symbol=trade.symbol.strip().upper(),
                        trade_index=index,
                    )
                )

    exposures = aggregate_exposure(trade_list)
    if limits.max_symbol_gross_notional is not None:
        for exposure in exposures:
            if exposure.gross_notional > limits.max_symbol_gross_notional:
                breaches.append(
                    RiskBreach(
                        code="max_symbol_gross_notional",
                        message=f"{exposure.symbol} exceeds maximum symbol gross notional.",
                        actual=exposure.gross_notional,
                        limit=limits.max_symbol_gross_notional,
                        symbol=exposure.symbol,
                    )
                )

    if limits.max_gross_notional is not None:
        actual = sum(exposure.gross_notional for exposure in exposures)
        if actual > limits.max_gross_notional:
            breaches.append(
                RiskBreach(
                    code="max_gross_notional",
                    message="Portfolio exceeds maximum gross notional.",
                    actual=actual,
                    limit=limits.max_gross_notional,
                )
            )

    return tuple(breaches)
