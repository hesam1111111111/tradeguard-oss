from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable

from .models import Trade


@dataclass(frozen=True, slots=True)
class DuplicateTrade:
    first_index: int
    duplicate_index: int


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def canonical_trade(trade: Trade) -> dict[str, object]:
    """Return a stable, JSON-serializable representation of a trade."""
    return {
        "closed_at": _timestamp(trade.closed_at),
        "entry": trade.entry,
        "exit": trade.exit,
        "opened_at": _timestamp(trade.opened_at),
        "quantity": trade.quantity,
        "side": trade.side.strip().lower(),
        "stop_loss": trade.stop_loss,
        "symbol": trade.symbol.strip().upper(),
    }


def journal_fingerprint(trades: Iterable[Trade]) -> str:
    """Return a SHA-256 fingerprint for an ordered journal."""
    payload = [canonical_trade(trade) for trade in trades]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def find_duplicate_trades(trades: Iterable[Trade]) -> list[DuplicateTrade]:
    """Find exact duplicate canonical trade records while preserving first occurrence."""
    seen: dict[str, int] = {}
    duplicates: list[DuplicateTrade] = []
    for index, trade in enumerate(trades):
        key = json.dumps(canonical_trade(trade), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if key in seen:
            duplicates.append(DuplicateTrade(seen[key], index))
        else:
            seen[key] = index
    return duplicates
