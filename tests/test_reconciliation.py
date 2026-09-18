from tradeguard.models import Trade
from tradeguard.reconciliation import reconcile_journals, reconciliation_fingerprint


def test_reordered_identical_journals_reconcile_cleanly():
    a = Trade("BTCUSDT", "long", 100, 110, stop_loss=95, quantity=2)
    b = Trade("ETHUSDT", "short", 50, 45, stop_loss=55, quantity=1)
    result = reconcile_journals([a, b], [b, a])
    assert result.clean is True
    assert result.exact_matches == 2
    assert result.modified_rows == 0
    assert result.missing == ()
    assert result.unexpected == ()
    assert result.reference_fingerprint == result.candidate_fingerprint


def test_reconciliation_preserves_duplicate_multiplicity():
    trade = Trade("BTCUSDT", "long", 100, 110)
    result = reconcile_journals([trade, trade], [trade])
    assert result.clean is False
    assert result.exact_matches == 1
    assert len(result.missing) == 1
    assert result.missing[0].count == 1
    assert result.unexpected == ()


def test_unique_identity_reports_field_level_mismatch():
    reference = Trade(
        "BTCUSDT",
        "long",
        100,
        110,
        stop_loss=95,
        quantity=2,
    )
    candidate = Trade(
        "BTCUSDT",
        "long",
        100,
        108,
        stop_loss=94,
        quantity=2,
    )
    result = reconcile_journals([reference], [candidate])
    assert result.clean is False
    assert result.modified_rows == 1
    assert result.missing == ()
    assert result.unexpected == ()
    assert [item.field for item in result.mismatches] == ["exit", "stop_loss"]


def test_ambiguous_identity_is_not_fuzzily_paired():
    reference = [
        Trade("BTCUSDT", "long", 100, 110),
        Trade("BTCUSDT", "long", 101, 111),
    ]
    candidate = [
        Trade("BTCUSDT", "long", 100, 109),
        Trade("BTCUSDT", "long", 101, 112),
    ]
    result = reconcile_journals(reference, candidate)
    assert result.modified_rows == 0
    assert result.mismatches == ()
    assert sum(delta.count for delta in result.missing) == 2
    assert sum(delta.count for delta in result.unexpected) == 2


def test_order_independent_fingerprint_changes_on_content_drift():
    a = Trade("BTCUSDT", "long", 100, 110)
    b = Trade("ETHUSDT", "short", 50, 45)
    assert reconciliation_fingerprint([a, b]) == reconciliation_fingerprint([b, a])
    assert reconciliation_fingerprint([a, b]) != reconciliation_fingerprint([a])
