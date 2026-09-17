from datetime import datetime, timezone

import pytest

from tradeguard.analytics import analyze_by_closed_period, analyze_trades
from tradeguard.models import Trade


def _trade(symbol, pnl_entry, pnl_exit, closed_at):
    return Trade(symbol=symbol, side="long", entry=pnl_entry, exit=pnl_exit, closed_at=closed_at)


def test_daily_segments_are_sorted_and_reconcile_when_complete():
    trades = [
        _trade("ETHUSDT", 50.0, 55.0, datetime(2026, 9, 2, 10, 0)),
        _trade("BTCUSDT", 100.0, 110.0, datetime(2026, 9, 1, 20, 0)),
        _trade("SOLUSDT", 20.0, 18.0, datetime(2026, 9, 2, 8, 0)),
    ]
    result = analyze_by_closed_period(trades, "day")
    assert result.basis == "recorded_closed_at_no_timezone_conversion"
    assert result.period == "day"
    assert result.complete is True
    assert result.measured_trades == 3
    assert [segment.key for segment in result.segments] == ["2026-09-01", "2026-09-02"]
    assert sum(segment.metrics.net_pnl for segment in result.segments) == analyze_trades(trades).net_pnl


def test_monthly_segments_are_deterministic():
    trades = [
        _trade("BTCUSDT", 100.0, 110.0, datetime(2026, 10, 1, 0, 0)),
        _trade("ETHUSDT", 50.0, 55.0, datetime(2026, 9, 30, 23, 59)),
    ]
    result = analyze_by_closed_period(trades, "month")
    assert [segment.key for segment in result.segments] == ["2026-09", "2026-10"]


def test_missing_close_time_is_explicit_and_never_fabricates_period():
    trades = [
        _trade("BTCUSDT", 100.0, 110.0, datetime(2026, 9, 1, 20, 0)),
        _trade("ETHUSDT", 50.0, 55.0, None),
    ]
    result = analyze_by_closed_period(trades)
    assert result.complete is False
    assert result.measured_trades == 1
    assert [segment.key for segment in result.segments] == ["2026-09-01"]
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "missing_closed_at"
    assert result.diagnostics[0].trade_index == 1
    assert result.diagnostics[0].symbol == "ETHUSDT"


def test_timezone_aware_timestamp_is_not_silently_converted():
    trade = _trade("BTCUSDT", 100.0, 110.0, datetime(2026, 9, 2, 0, 30, tzinfo=timezone.utc))
    result = analyze_by_closed_period([trade])
    assert result.segments[0].key == "2026-09-02"


def test_invalid_period_is_rejected_even_for_empty_input():
    with pytest.raises(ValueError, match="period"):
        analyze_by_closed_period([], "week")


def test_empty_temporal_analysis_is_deterministic():
    result = analyze_by_closed_period([])
    assert result.measured_trades == 0
    assert result.segments == ()
    assert result.diagnostics == ()
    assert result.complete is True
