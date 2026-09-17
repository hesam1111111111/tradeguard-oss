import pytest

from tradeguard.models import Trade
from tradeguard.risk import RiskLimits, aggregate_exposure, check_risk_limits, trade_notional


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
    trade = Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=2.0)
    assert trade_notional(trade) == 200.0


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), float("-inf")])
def test_risk_limits_require_positive_finite_values(value):
    with pytest.raises(ValueError, match="positive finite"):
        RiskLimits(max_gross_notional=value)


@pytest.mark.parametrize(
    ("entry", "quantity", "field"),
    [
        (0.0, 1.0, "trade.entry"),
        (-1.0, 1.0, "trade.entry"),
        (float("nan"), 1.0, "trade.entry"),
        (float("inf"), 1.0, "trade.entry"),
        (100.0, 0.0, "trade.quantity"),
        (100.0, -1.0, "trade.quantity"),
        (100.0, float("nan"), "trade.quantity"),
        (100.0, float("inf"), "trade.quantity"),
    ],
)
def test_trade_notional_rejects_invalid_direct_api_inputs(entry, quantity, field):
    trade = Trade(symbol="BTCUSDT", side="long", entry=entry, exit=110.0, quantity=quantity)
    with pytest.raises(ValueError, match=field):
        trade_notional(trade)


def test_aggregate_exposure_rejects_blank_symbol():
    trade = Trade(symbol="   ", side="long", entry=100.0, exit=110.0, quantity=1.0)
    with pytest.raises(ValueError, match="symbol"):
        aggregate_exposure([trade])


def test_aggregate_exposure_rejects_invalid_side():
    trade = Trade(symbol="BTCUSDT", side="buy", entry=100.0, exit=110.0, quantity=1.0)
    with pytest.raises(ValueError, match="Side"):
        aggregate_exposure([trade])


def test_risk_limits_report_trade_symbol_and_portfolio_breaches():
    trades = [
        Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=2.0),
        Trade(symbol="BTCUSDT", side="short", entry=120.0, exit=115.0, quantity=1.0),
        Trade(symbol="ETHUSDT", side="long", entry=50.0, exit=55.0, quantity=3.0),
    ]
    limits = RiskLimits(
        max_trade_notional=180.0,
        max_symbol_gross_notional=300.0,
        max_gross_notional=450.0,
    )

    breaches = check_risk_limits(trades, limits)

    assert [breach.code for breach in breaches] == [
        "max_trade_notional",
        "max_symbol_gross_notional",
        "max_gross_notional",
    ]
    assert breaches[0].trade_index == 0
    assert breaches[1].symbol == "BTCUSDT"
    assert breaches[2].actual == 470.0


def test_equal_to_limit_is_not_a_breach():
    trades = [Trade(symbol="BTCUSDT", side="long", entry=100.0, exit=110.0, quantity=2.0)]
    assert check_risk_limits(trades, RiskLimits(max_gross_notional=200.0)) == ()
