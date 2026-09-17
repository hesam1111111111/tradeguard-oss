import pytest

from tradeguard.models import Trade
from tradeguard.risk import (
    RiskBudget,
    RiskLimits,
    aggregate_exposure,
    analyze_initial_risk,
    check_risk_limits,
    evaluate_risk_budget,
    trade_initial_risk,
    trade_notional,
)


def test_aggregate_exposure_normalizes_symbol_and_side():
    trades = [
        Trade(symbol="btcusdt", side="long", entry=100.0, exit=110.0, quantity=2.0),
        Trade(symbol=" BTCUSDT ", side="short", entry=120.0, exit=115.0, quantity=1.0),
        Trade(symbol="ETHUSDT", side="long", entry=50.0, exit=55.0, quantity=3.0),
    ]
    exposures = aggregate_exposure(trades)
    assert [item.symbol for item in exposures] == ["BTCUSDT", "ETHUSDT"]
    btc = exposures[0]
    assert btc.long_notional == 200.0
    assert btc.short_notional == 120.0
    assert btc.gross_notional == 320.0
    assert btc.net_notional == 80.0


def test_trade_notional_uses_entry_price_and_quantity():
    assert trade_notional(Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=2.0)) == 200.0


def test_trade_initial_risk_is_stop_distance_times_quantity():
    trade = Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=95.0, quantity=2.0)
    assert trade_initial_risk(trade) == 10.0


def test_trade_initial_risk_is_direction_agnostic_distance():
    trade = Trade(symbol="BTCUSDT", side="short", entry=100.0, exit=90.0, stop_loss=105.0, quantity=3.0)
    assert trade_initial_risk(trade) == 15.0


@pytest.mark.parametrize("stop_loss", [0.0, -1.0, float("nan"), float("inf"), float("-inf")])
def test_trade_initial_risk_rejects_invalid_stop(stop_loss):
    trade = Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=stop_loss, quantity=1.0)
    with pytest.raises(ValueError, match="stop_loss"):
        trade_initial_risk(trade)


def test_trade_initial_risk_requires_stop():
    trade = Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=1.0)
    with pytest.raises(ValueError, match="required"):
        trade_initial_risk(trade)


def test_trade_initial_risk_rejects_zero_distance_stop():
    trade = Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=100.0, quantity=1.0)
    with pytest.raises(ValueError, match="differ"):
        trade_initial_risk(trade)


def test_analyze_initial_risk_returns_structured_diagnostics_for_unmeasurable_trades():
    trades = [
        Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=95.0, quantity=2.0),
        Trade(symbol="ETHUSDT", side="long", entry=50.0, exit=55.0, quantity=1.0),
        Trade(symbol="SOLUSDT", side="short", entry=20.0, exit=18.0, stop_loss=20.0, quantity=4.0),
    ]
    result = analyze_initial_risk(trades)
    assert result.total_initial_risk == 10.0
    assert result.measured_trades == 1
    assert [item.trade_index for item in result.diagnostics] == [1, 2]
    assert [item.symbol for item in result.diagnostics] == ["ETHUSDT", "SOLUSDT"]
    assert all(item.code == "unusable_initial_risk" for item in result.diagnostics)


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), float("-inf")])
def test_risk_limits_require_positive_finite_values(value):
    with pytest.raises(ValueError, match="positive finite"):
        RiskLimits(max_gross_notional=value)


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), float("-inf")])
def test_risk_budget_requires_positive_finite_values(value):
    with pytest.raises(ValueError, match="positive finite"):
        RiskBudget(max_trade_initial_risk=value)
    with pytest.raises(ValueError, match="positive finite"):
        RiskBudget(max_total_initial_risk=value)


def test_risk_budget_reports_trade_then_total_breach_deterministically():
    trades = [
        Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=90.0, quantity=2.0),
        Trade(symbol="ETHUSDT", side="short", entry=50.0, exit=45.0, stop_loss=55.0, quantity=1.0),
    ]
    result = evaluate_risk_budget(trades, RiskBudget(max_trade_initial_risk=15.0, max_total_initial_risk=20.0))
    assert result.total_initial_risk == 25.0
    assert result.measured_trades == 2
    assert result.diagnostics == ()
    assert [item.code for item in result.breaches] == ["max_trade_initial_risk", "max_total_initial_risk"]
    assert result.breaches[0].trade_index == 0
    assert result.breaches[0].symbol == "BTCUSDT"
    assert result.breaches[1].actual == 25.0


def test_risk_budget_missing_stop_is_explicit_and_suppresses_total_verdict():
    trades = [
        Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=90.0, quantity=2.0),
        Trade(symbol="ETHUSDT", side="long", entry=50.0, exit=55.0, quantity=1.0),
    ]
    result = evaluate_risk_budget(trades, RiskBudget(max_trade_initial_risk=15.0, max_total_initial_risk=10.0))
    assert result.total_initial_risk == 20.0
    assert result.measured_trades == 1
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].trade_index == 1
    assert [item.code for item in result.breaches] == ["max_trade_initial_risk"]


@pytest.mark.parametrize(
    ("entry", "quantity", "field"),
    [(0.0, 1.0, "trade.entry"), (-1.0, 1.0, "trade.entry"), (float("nan"), 1.0, "trade.entry"), (float("inf"), 1.0, "trade.entry"), (100.0, 0.0, "trade.quantity"), (100.0, -1.0, "trade.quantity"), (100.0, float("nan"), "trade.quantity"), (100.0, float("inf"), "trade.quantity")],
)
def test_trade_notional_rejects_invalid_direct_api_inputs(entry, quantity, field):
    trade = Trade(symbol="BTCUSDT", side="long", entry=entry, exit=110.0, quantity=quantity)
    with pytest.raises(ValueError, match=field):
        trade_notional(trade)


def test_aggregate_exposure_rejects_blank_symbol():
    with pytest.raises(ValueError, match="symbol"):
        aggregate_exposure([Trade(symbol="   ", side="long", entry=100.0, exit=110.0, quantity=1.0)])


def test_aggregate_exposure_rejects_invalid_side():
    with pytest.raises(ValueError, match="Side"):
        aggregate_exposure([Trade(symbol="BTCUSDT", side="buy", entry=100.0, exit=110.0, quantity=1.0)])


def test_risk_limits_report_trade_symbol_and_portfolio_breaches():
    trades = [
        Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=2.0),
        Trade(symbol="BTCUSDT", side="short", entry=120.0, exit=115.0, quantity=1.0),
        Trade(symbol="ETHUSDT", side="long", entry=50.0, exit=55.0, quantity=3.0),
    ]
    limits = RiskLimits(max_trade_notional=180.0, max_symbol_gross_notional=300.0, max_gross_notional=450.0)
    breaches = check_risk_limits(trades, limits)
    assert [breach.code for breach in breaches] == ["max_trade_notional", "max_symbol_gross_notional", "max_gross_notional"]
    assert breaches[0].trade_index == 0
    assert breaches[1].symbol == "BTCUSDT"
    assert breaches[2].actual == 470.0


def test_equal_to_limit_is_not_a_breach():
    trades = [Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=2.0)]
    assert check_risk_limits(trades, RiskLimits(max_gross_notional=200.0)) == ()


def test_risk_budget_equal_to_limits_is_not_a_breach():
    trades = [Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, stop_loss=90.0, quantity=2.0)]
    result = evaluate_risk_budget(trades, RiskBudget(max_trade_initial_risk=20.0, max_total_initial_risk=20.0))
    assert result.breaches == ()
