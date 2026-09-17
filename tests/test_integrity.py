from datetime import datetime

from tradeguard.integrity import find_duplicate_trades, journal_fingerprint
from tradeguard.models import Trade


def test_journal_fingerprint_is_stable_for_equivalent_normalized_trades():
    first = [Trade(" btcusdt ", " LONG ", 100, 110, 95, 2, datetime(2026, 1, 1), datetime(2026, 1, 2))]
    second = [Trade("BTCUSDT", "long", 100, 110, 95, 2, datetime(2026, 1, 1), datetime(2026, 1, 2))]

    assert journal_fingerprint(first) == journal_fingerprint(second)
    assert len(journal_fingerprint(first)) == 64


def test_journal_fingerprint_changes_when_trade_data_changes():
    original = [Trade("BTCUSDT", "long", 100, 110, 95, 1)]
    changed = [Trade("BTCUSDT", "long", 100, 111, 95, 1)]

    assert journal_fingerprint(original) != journal_fingerprint(changed)


def test_journal_fingerprint_preserves_order():
    first = Trade("BTCUSDT", "long", 100, 110, 95, 1)
    second = Trade("ETHUSDT", "short", 200, 190, 210, 1)

    assert journal_fingerprint([first, second]) != journal_fingerprint([second, first])


def test_duplicate_detection_reports_first_and_duplicate_indices():
    first = Trade("BTCUSDT", "long", 100, 110, 95, 1)
    equivalent = Trade(" btcusdt ", " LONG ", 100, 110, 95, 1)
    distinct = Trade("BTCUSDT", "long", 100, 111, 95, 1)

    duplicates = find_duplicate_trades([first, distinct, equivalent, equivalent])

    assert [(item.first_index, item.duplicate_index) for item in duplicates] == [(0, 2), (0, 3)]
