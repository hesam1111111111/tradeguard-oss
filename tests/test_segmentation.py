import pytest

from tradeguard.analytics import analyze_by_side, analyze_by_symbol, analyze_trades
from tradeguard.models import Trade


def _trades():
    return [
        Trade(symbol="ethusdt", side="short", entry=50.0, exit=45.0, quantity=1.0),
        Trade(symbol=" BTCUSDT ", side="LONG", entry=100.0, exit=110.0, quantity=2.0),
        Trade(symbol="btcusdt", side="short", entry=120.0, exit=125.0, quantity=1.0),
    ]


def test_symbol_segments_are_normalized_sorted_and_preserve_aggregate_pnl():
    trades = _trades()
    segments = analyze_by_symbol(trades)
    assert [segment.key for segment in segments] == ["BTCUSDT", "ETHUSDT"]
    assert [segment.metrics.trades for segment in segments] == [2, 1]
    assert sum(segment.metrics.net_pnl for segment in segments) == analyze_trades(trades).net_pnl
    assert segments[0].metrics.net_pnl == 15.0
    assert segments[1].metrics.net_pnl == 5.0


def test_side_segments_are_normalized_sorted_and_preserve_aggregate_pnl():
    trades = _trades()
    segments = analyze_by_side(trades)
    assert [segment.key for segment in segments] == ["long", "short"]
    assert [segment.metrics.trades for segment in segments] == [1, 2]
    assert sum(segment.metrics.net_pnl for segment in segments) == analyze_trades(trades).net_pnl


def test_symbol_segmentation_rejects_blank_symbol():
    trade = Trade(symbol="   ", side="long", entry=100.0, exit=110.0, quantity=1.0)
    with pytest.raises(ValueError, match="symbol"):
        analyze_by_symbol([trade])


def test_side_segmentation_rejects_invalid_side():
    trade = Trade(symbol="BTCUSDT", side="buy", entry=100.0, exit=110.0, quantity=1.0)
    with pytest.raises(ValueError, match="Side"):
        analyze_by_side([trade])


def test_empty_segmentation_is_deterministic():
    assert analyze_by_symbol([]) == ()
    assert analyze_by_side([]) == ()
