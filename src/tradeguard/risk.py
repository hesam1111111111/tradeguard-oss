from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from .models import Trade


def _require_positive_finite(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")


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
class InitialRiskDiagnostic:
    code: str
    message: str
    trade_index: int
    symbol: str


@dataclass(frozen=True, slots=True)
class InitialRiskAnalysis:
    total_initial_risk: float
    measured_trades: int
    diagnostics: tuple[InitialRiskDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class RiskBudget:
    max_trade_initial_risk: float | None = None
    max_total_initial_risk: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("max_trade_initial_risk", self.max_trade_initial_risk),
            ("max_total_initial_risk", self.max_total_initial_risk),
        ):
            if value is not None:
                _require_positive_finite(name, value)


@dataclass(frozen=True, slots=True)
class RiskBudgetBreach:
    code: str
    message: str
    actual: float
    limit: float
    symbol: str | None = None
    trade_index: int | None = None


@dataclass(frozen=True, slots=True)
class RiskBudgetEvaluation:
    total_initial_risk: float
    measured_trades: int
    diagnostics: tuple[InitialRiskDiagnostic, ...]
    breaches: tuple[RiskBudgetBreach, ...]


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
            if value is not None:
                _require_positive_finite(name, value)


@dataclass(frozen=True, slots=True)
class RiskBreach:
    code: str
    message: str
    actual: float
    limit: float
    symbol: str | None = None
    trade_index: int | None = None


def trade_notional(trade: Trade) -> float:
    """Return validated entry-price notional for a trade."""
    _require_positive_finite("trade.entry", trade.entry)
    _require_positive_finite("trade.quantity", trade.quantity)
    return trade.entry * trade.quantity


def trade_initial_risk(trade: Trade) -> float:
    """Return stop-based initial risk for a trade.

    Initial risk is distinct from notional exposure and requires a usable stop loss.
    """
    _require_positive_finite("trade.entry", trade.entry)
    _require_positive_finite("trade.quantity", trade.quantity)
    if trade.stop_loss is None:
        raise ValueError("trade.stop_loss is required for initial risk")
    _require_positive_finite("trade.stop_loss", trade.stop_loss)
    if trade.stop_loss == trade.entry:
        raise ValueError("trade.stop_loss must differ from trade.entry")
    return abs(trade.entry - trade.stop_loss) * trade.quantity


def analyze_initial_risk(trades: Iterable[Trade]) -> InitialRiskAnalysis:
    """Analyze stop-based initial risk and diagnose trades that cannot be measured."""
    total = 0.0
    measured = 0
    diagnostics: list[InitialRiskDiagnostic] = []

    for index, trade in enumerate(trades):
        symbol = trade.symbol.strip().upper()
        if not symbol:
            symbol = "<UNKNOWN>"
        try:
            risk = trade_initial_risk(trade)
        except (TypeError, ValueError) as exc:
            diagnostics.append(
                InitialRiskDiagnostic(
                    code="unusable_initial_risk",
                    message=str(exc),
                    trade_index=index,
                    symbol=symbol,
                )
            )
            continue
        total += risk
        measured += 1

    return InitialRiskAnalysis(total, measured, tuple(diagnostics))


def evaluate_risk_budget(trades: Iterable[Trade], budget: RiskBudget) -> RiskBudgetEvaluation:
    """Evaluate deterministic stop-based historical risk budgets.

    Unmeasurable trades remain explicit diagnostics and never contribute zero risk.
    """
    trade_list = tuple(trades)
    analysis = analyze_initial_risk(trade_list)
    breaches: list[RiskBudgetBreach] = []

    if budget.max_trade_initial_risk is not None:
        for index, trade in enumerate(trade_list):
            try:
                actual = trade_initial_risk(trade)
            except (TypeError, ValueError):
                continue
            if actual > budget.max_trade_initial_risk:
                symbol = trade.symbol.strip().upper() or "<UNKNOWN>"
                breaches.append(RiskBudgetBreach(
                    code="max_trade_initial_risk",
                    message=f"Trade {index} exceeds maximum initial risk.",
                    actual=actual,
                    limit=budget.max_trade_initial_risk,
                    symbol=symbol,
                    trade_index=index,
                ))

    # A total-budget verdict is only meaningful when every supplied trade is measurable.
    if budget.max_total_initial_risk is not None and not analysis.diagnostics:
        if analysis.total_initial_risk > budget.max_total_initial_risk:
            breaches.append(RiskBudgetBreach(
                code="max_total_initial_risk",
                message="Journal exceeds maximum total initial risk.",
                actual=analysis.total_initial_risk,
                limit=budget.max_total_initial_risk,
            ))

    return RiskBudgetEvaluation(
        total_initial_risk=analysis.total_initial_risk,
        measured_trades=analysis.measured_trades,
        diagnostics=analysis.diagnostics,
        breaches=tuple(breaches),
    )


def aggregate_exposure(trades: Iterable[Trade]) -> tuple[Exposure, ...]:
    """Aggregate validated entry notional by normalized symbol and side.

    This is deliberately price-at-entry exposure, not live mark-to-market exposure.
    """
    totals: dict[str, list[float]] = {}
    for trade in trades:
        symbol = trade.symbol.strip().upper()
        if not symbol:
            raise ValueError("trade.symbol must not be empty")
        side = trade.normalized_side
        notional = trade_notional(trade)
        long_short = totals.setdefault(symbol, [0.0, 0.0])
        if side == "long":
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
                breaches.append(RiskBreach("max_trade_notional", f"Trade {index} exceeds maximum trade notional.", actual, limits.max_trade_notional, trade.symbol.strip().upper(), index))

    exposures = aggregate_exposure(trade_list)
    if limits.max_symbol_gross_notional is not None:
        for exposure in exposures:
            if exposure.gross_notional > limits.max_symbol_gross_notional:
                breaches.append(RiskBreach("max_symbol_gross_notional", f"{exposure.symbol} exceeds maximum symbol gross notional.", exposure.gross_notional, limits.max_symbol_gross_notional, exposure.symbol))

    if limits.max_gross_notional is not None:
        actual = sum(exposure.gross_notional for exposure in exposures)
        if actual > limits.max_gross_notional:
            breaches.append(RiskBreach("max_gross_notional", "Portfolio exceeds maximum gross notional.", actual, limits.max_gross_notional))

    return tuple(breaches)
