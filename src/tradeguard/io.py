from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path

from .models import Trade
from .schema import validate_columns


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def source_file_fingerprint(path: str | Path) -> str:
    """Return SHA-256 for the exact bytes of a local source artifact."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_trades_csv(path: str | Path) -> list[Trade]:
    trades: list[Trade] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        raw_fieldnames = reader.fieldnames or []
        normalized_fieldnames = [column.strip() for column in raw_fieldnames]
        if len(normalized_fieldnames) != len(set(normalized_fieldnames)):
            raise ValueError("CSV columns must be unique after trimming whitespace")
        missing = validate_columns(normalized_fieldnames)
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")
        reader.fieldnames = normalized_fieldnames

        for row_number, row in enumerate(reader, start=2):
            try:
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
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid value in CSV row {row_number}: {exc}") from exc
    return trades
