from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from .integrity import canonical_trade
from .models import Trade

_IDENTITY_FIELDS = ("symbol", "side", "opened_at", "closed_at")
_ALL_FIELDS = ("symbol", "side", "entry", "exit", "stop_loss", "quantity", "opened_at", "closed_at")


@dataclass(frozen=True, slots=True)
class RecordDelta:
    record: tuple[tuple[str, object], ...]
    count: int


@dataclass(frozen=True, slots=True)
class FieldMismatch:
    identity: tuple[tuple[str, object], ...]
    field: str
    reference_value: object
    candidate_value: object


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    reference_fingerprint: str
    candidate_fingerprint: str
    reference_rows: int
    candidate_rows: int
    exact_matches: int
    modified_rows: int
    missing: tuple[RecordDelta, ...]
    unexpected: tuple[RecordDelta, ...]
    mismatches: tuple[FieldMismatch, ...]

    @property
    def clean(self) -> bool:
        return not self.missing and not self.unexpected and not self.mismatches


def _canonical_tuple(trade: Trade) -> tuple[tuple[str, object], ...]:
    record = canonical_trade(trade)
    return tuple((field, record[field]) for field in _ALL_FIELDS)


def _identity(record: tuple[tuple[str, object], ...]) -> tuple[tuple[str, object], ...]:
    values = dict(record)
    return tuple((field, values[field]) for field in _IDENTITY_FIELDS)


def _record_json(record: tuple[tuple[str, object], ...]) -> str:
    return json.dumps(dict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def reconciliation_fingerprint(trades: Iterable[Trade]) -> str:
    """Return an order-independent SHA-256 fingerprint for a journal."""
    records = sorted(_record_json(_canonical_tuple(trade)) for trade in trades)
    encoded = json.dumps(records, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expanded(counter: Counter[tuple[tuple[str, object], ...]]) -> list[tuple[tuple[str, object], ...]]:
    rows: list[tuple[tuple[str, object], ...]] = []
    for record in sorted(counter, key=_record_json):
        rows.extend([record] * counter[record])
    return rows


def _deltas(counter: Counter[tuple[tuple[str, object], ...]]) -> tuple[RecordDelta, ...]:
    return tuple(RecordDelta(record=record, count=counter[record]) for record in sorted(counter, key=_record_json))


def reconcile_journals(reference: Iterable[Trade], candidate: Iterable[Trade]) -> ReconciliationResult:
    """Deterministically reconcile two journals without fuzzy matching.

    Exact records are cancelled first. Remaining records are paired only when the
    identity tuple (symbol, side, opened_at, closed_at) is unique on both sides.
    Ambiguous records remain explicit missing/unexpected deltas.
    """
    reference_rows = list(reference)
    candidate_rows = list(candidate)

    reference_counter = Counter(_canonical_tuple(trade) for trade in reference_rows)
    candidate_counter = Counter(_canonical_tuple(trade) for trade in candidate_rows)

    exact_matches = sum((reference_counter & candidate_counter).values())
    remaining_reference = reference_counter - candidate_counter
    remaining_candidate = candidate_counter - reference_counter

    ref_by_identity: dict[tuple[tuple[str, object], ...], list[tuple[tuple[str, object], ...]]] = defaultdict(list)
    cand_by_identity: dict[tuple[tuple[str, object], ...], list[tuple[tuple[str, object], ...]]] = defaultdict(list)
    for record in _expanded(remaining_reference):
        ref_by_identity[_identity(record)].append(record)
    for record in _expanded(remaining_candidate):
        cand_by_identity[_identity(record)].append(record)

    mismatches: list[FieldMismatch] = []
    modified_rows = 0
    for identity in sorted(set(ref_by_identity) & set(cand_by_identity), key=lambda value: json.dumps(dict(value), sort_keys=True, default=str)):
        ref_records = ref_by_identity[identity]
        cand_records = cand_by_identity[identity]
        if len(ref_records) != 1 or len(cand_records) != 1:
            continue
        ref_record = ref_records[0]
        cand_record = cand_records[0]
        ref_values = dict(ref_record)
        cand_values = dict(cand_record)
        changed = [field for field in _ALL_FIELDS if ref_values[field] != cand_values[field]]
        if not changed:
            continue
        modified_rows += 1
        for field in changed:
            mismatches.append(
                FieldMismatch(
                    identity=identity,
                    field=field,
                    reference_value=ref_values[field],
                    candidate_value=cand_values[field],
                )
            )
        remaining_reference[ref_record] -= 1
        if remaining_reference[ref_record] <= 0:
            del remaining_reference[ref_record]
        remaining_candidate[cand_record] -= 1
        if remaining_candidate[cand_record] <= 0:
            del remaining_candidate[cand_record]

    mismatches.sort(
        key=lambda item: (
            json.dumps(dict(item.identity), sort_keys=True, default=str),
            item.field,
        )
    )

    return ReconciliationResult(
        reference_fingerprint=reconciliation_fingerprint(reference_rows),
        candidate_fingerprint=reconciliation_fingerprint(candidate_rows),
        reference_rows=len(reference_rows),
        candidate_rows=len(candidate_rows),
        exact_matches=exact_matches,
        modified_rows=modified_rows,
        missing=_deltas(remaining_reference),
        unexpected=_deltas(remaining_candidate),
        mismatches=tuple(mismatches),
    )
