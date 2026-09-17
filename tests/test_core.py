import pytest

from tradeguard import Trade, analyze_trades, validate_trades


def test_long_trade_metrics_and_r_multiple():
    trade = Trade(symbol="BTCUSDT", side="long", entry=100, exit=110, stop_loss=95, quantity=2)
    metrics = analyze_trades([trade])

    assert trade.pnl == 20
    assert trade.initial_risk == 10
    assert trade.r_multiple == 2
    assert metrics.trades == 1
    assert metrics.wins == 1
    assert metrics.win_rate == 1.0
    assert metrics.net_pnl == 20
    assert metrics.max_drawdown == 0
    assert metrics.average_r_multiple == 2
    assert metrics.best_trade == 20
    assert metrics.worst_trade == 20


def test_short_trade_pnl_is_directionally_correct():
    trade = Trade(symbol="ETHUSDT", side="short", entry=100, exit=90, stop_loss=105, quantity=3)
    assert trade.pnl == 30
    assert trade.initial_risk == 15
    assert trade.r_multiple == 2


def test_invalid_side_is_not_silently_treated_as_short():
    trade = Trade(symbol="BTCUSDT", side="flat", entry=100, exit=90, stop_loss=105)
    issues = validate_trades([trade])
    assert any(i.code == "invalid_side" for i in issues)
    with pytest.raises(ValueError, match="Side must be"):
        _ = trade.pnl


def test_drawdown_and_profit_factor():
    trades = [
        Trade("A", "long", 100, 110, 95),
        Trade("B", "long", 100, 92, 95),
        Trade("C", "long", 100, 96, 95),
    ]
    metrics = analyze_trades(trades)
    assert metrics.max_drawdown == 12
    assert metrics.gross_profit == 10
    assert metrics.gross_loss == 12
    assert metrics.profit_factor == pytest.approx(10 / 12)
    assert metrics.best_trade == 10
    assert metrics.worst_trade == -8


def test_breakeven_trade_is_counted_separately():
    metrics = analyze_trades([Trade("A", "long", 100, 100, 95)])
    assert metrics.breakeven == 1
    assert metrics.wins == 0
    assert metrics.losses == 0
    assert metrics.profit_factor is None


def test_missing_stop_loss_is_warning():
    issues = validate_trades([Trade("BTCUSDT", "long", 100, 110, None)])
    assert any(i.code == "missing_stop_loss" and i.severity == "warning" for i in issues)


def test_invalid_short_stop_loss_is_error():
    issues = validate_trades([Trade("ETHUSDT", "short", 100, 90, 95)])
    assert any(i.code == "invalid_stop_loss" and i.severity == "error" for i in issues)
