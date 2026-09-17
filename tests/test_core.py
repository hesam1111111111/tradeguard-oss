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


def test_drawdown_is_peak_to_trough_on_closed_trade_pnl():
    trades = [
        Trade("A", "long", 100, 110, 95),
        Trade("B", "long", 100, 92, 95),
        Trade("C", "long", 100, 96, 95),
    ]
    metrics = analyze_trades(trades)
    assert metrics.max_drawdown == 12


def test_missing_stop_loss_is_warning():
    issues = validate_trades([Trade("BTCUSDT", "long", 100, 110, None)])
    assert any(i.code == "missing_stop_loss" and i.severity == "warning" for i in issues)


def test_invalid_short_stop_loss_is_error():
    issues = validate_trades([Trade("ETHUSDT", "short", 100, 90, 95)])
    assert any(i.code == "invalid_stop_loss" and i.severity == "error" for i in issues)
