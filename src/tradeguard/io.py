from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import Trade


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def load_trades_csv(path: str | Path) -> list[Trade]:
    trades: list[Trade] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"symbol", "side", "entry", "exit"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            stop_loss = row.get("stop_loss")
            quantity = row.get("quantity")
            trades.append(
                Trade(
                    symbol=(row.get("symbol") or "").strip(),
                    side=(row.get("side") or "").strip(),
                    entry=float(row["entry"]),
                    exit=float(row["exit"]),
                    stop_loss=float(stop_loss) if stop_loss else None,
                    quantity=float(quantity) if quantity else 1.0,
                    opened_at=_parse_optional_datetime(row.get("opened_at")),
                    closed_at=_parse_optional_datetime(row.get("closed_at")),
                )
            )
    return trades
