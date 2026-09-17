from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from .models import Trade

_CANONICAL_FIELDS = (
    "symbol",
    "side",
    "entry",
    "exit",
    "stop_loss",
    "quantity",
    "opened_at",
    "closed_at",
)
_REQUIRED_FIELDS = ("symbol", "side", "entry", "exit")


@dataclass(frozen=True, slots=True)
class ImportDiagnostic:
    code: str
    message: str
    source_row: int | None = None
    field: str | None = None


@dataclass(frozen=True, slots=True)
class ImportResult:
    trades: tuple[Trade, ...]
    diagnostics: tuple[ImportDiagnostic, ...]
    source_rows: int
    imported_rows: int
    rejected_rows: int
    mapping: tuple[tuple[str, str], ...]

    @property
    def complete(self) -> bool:
        return self.rejected_rows == 0 and not self.diagnostics


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value in (None, ""):
        return None
    return datetime.fromisoformat(value)


def _validate_mapping(mapping: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    unknown = sorted(set(mapping) - set(_CANONICAL_FIELDS))
    if unknown:
        raise ValueError(f"Unknown canonical mapping fields: {', '.join(unknown)}")
    missing = [field for field in _REQUIRED_FIELDS if field not in mapping]
    if missing:
        raise ValueError(f"Missing required canonical mappings: {', '.join(missing)}")
    source_columns = [mapping[field] for field in mapping]
    if any(not column or not column.strip() for column in source_columns):
        raise ValueError("Mapped source column names must not be blank")
    if len(source_columns) != len(set(source_columns)):
        raise ValueError("Each source column may map to only one canonical field")
    return tuple((field, mapping[field]) for field in _CANONICAL_FIELDS if field in mapping)


def import_mapped_csv(path: str | Path, mapping: Mapping[str, str]) -> ImportResult:
    """Import a tabular CSV using an explicit source->canonical field mapping.

    The mapping keys are canonical TradeGuard fields and the values are exact
    source CSV column names. No aliases, guesses, or heuristic inference are
    performed.
    """
    normalized_mapping = _validate_mapping(mapping)
    trades: list[Trade] = []
    diagnostics: list[ImportDiagnostic] = []
    source_rows = 0
    rejected_rows = 0

    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_source_columns = [source for _, source in normalized_mapping if source not in fieldnames]
        if missing_source_columns:
            raise ValueError(f"Missing mapped source columns: {', '.join(sorted(missing_source_columns))}")

        for source_row, row in enumerate(reader, start=2):
            source_rows += 1
            try:
                get = lambda canonical: row[mapping[canonical]] if canonical in mapping else None
                stop_loss = get("stop_loss")
                quantity = get("quantity")
                trades.append(
                    Trade(
                        symbol=(get("symbol") or "").strip(),
                        side=(get("side") or "").strip(),
                        entry=float(get("entry")),
                        exit=float(get("exit")),
                        stop_loss=float(stop_loss) if stop_loss not in (None, "") else None,
                        quantity=float(quantity) if quantity not in (None, "") else 1.0,
                        opened_at=_parse_optional_datetime(get("opened_at")),
                        closed_at=_parse_optional_datetime(get("closed_at")),
                    )
                )
            except (TypeError, ValueError, KeyError) as exc:
                rejected_rows += 1
                diagnostics.append(
                    ImportDiagnostic(
                        code="invalid_mapped_row",
                        message=str(exc),
                        source_row=source_row,
                    )
                )

    return ImportResult(
        trades=tuple(trades),
        diagnostics=tuple(diagnostics),
        source_rows=source_rows,
        imported_rows=len(trades),
        rejected_rows=rejected_rows,
        mapping=normalized_mapping,
    )
