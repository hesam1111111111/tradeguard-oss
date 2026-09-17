from tradeguard.diagnostics import diagnose_journal
from tradeguard.models import Trade


def test_diagnostics_allows_warnings_but_counts_them():
    diagnostics = diagnose_journal([Trade("BTCUSDT", "long", 100, 110)])
    assert diagnostics.trade_count == 1
    assert diagnostics.error_count == 0
    assert diagnostics.warning_count == 1
    assert diagnostics.duplicate_count == 0
    assert diagnostics.valid_for_metrics is True
    assert len(diagnostics.fingerprint) == 64


def test_exact_duplicates_block_metrics():
    trade = Trade("BTCUSDT", "long", 100, 110, 95, 1)
    diagnostics = diagnose_journal([trade, trade])
    assert diagnostics.duplicate_count == 1
    assert diagnostics.valid_for_metrics is False
    assert diagnostics.duplicate_trades == ({"first_index": 0, "duplicate_index": 1},)


def test_validation_errors_block_metrics():
    diagnostics = diagnose_journal([Trade("", "long", 100, 110, 95, 1)])
    assert diagnostics.error_count == 1
    assert diagnostics.valid_for_metrics is False
