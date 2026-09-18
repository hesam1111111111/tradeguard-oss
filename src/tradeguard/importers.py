from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from .models import Trade

_CANONICAL_FIELDS = ("symbol","side","entry","exit","stop_loss","quantity","opened_at","closed_at")
_REQUIRED_FIELDS = ("symbol","side","entry","exit")
_NUMERIC_FIELDS = {"entry","exit","stop_loss","quantity"}
_DATETIME_FIELDS = {"opened_at","closed_at"}

@dataclass(frozen=True, slots=True)
class ImportDiagnostic:
    code: str
    message: str
    source_row: int | None = None
    field: str | None = None
    value: str | None = None

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

def _validate_mapping(mapping: Mapping[str,str]) -> tuple[tuple[str,str],...]:
    unknown=sorted(set(mapping)-set(_CANONICAL_FIELDS))
    if unknown: raise ValueError(f"Unknown canonical mapping fields: {', '.join(unknown)}")
    missing=[f for f in _REQUIRED_FIELDS if f not in mapping]
    if missing: raise ValueError(f"Missing required canonical mappings: {', '.join(missing)}")
    cols=[mapping[f] for f in mapping]
    if any(not c or not c.strip() for c in cols): raise ValueError("Mapped source column names must not be blank")
    if len(cols)!=len(set(cols)): raise ValueError("Each source column may map to only one canonical field")
    return tuple((f,mapping[f]) for f in _CANONICAL_FIELDS if f in mapping)

def _diagnose_row(row: dict[str,str], mapping: Mapping[str,str], source_row: int) -> tuple[ImportDiagnostic,...]:
    out=[]
    for field in _REQUIRED_FIELDS:
        value=row.get(mapping[field])
        if value is None or not value.strip():
            out.append(ImportDiagnostic("missing_required_value",f"Required mapped value for {field} is missing",source_row,field,value))
    for field in _NUMERIC_FIELDS:
        if field not in mapping: continue
        value=row.get(mapping[field])
        if value in (None,""):
            continue
        try: float(value)
        except (TypeError,ValueError):
            out.append(ImportDiagnostic("invalid_number",f"Mapped value for {field} is not a valid number",source_row,field,value))
    for field in _DATETIME_FIELDS:
        if field not in mapping: continue
        value=row.get(mapping[field])
        if value in (None,""): continue
        try: datetime.fromisoformat(value)
        except (TypeError,ValueError):
            out.append(ImportDiagnostic("invalid_datetime",f"Mapped value for {field} is not a valid ISO datetime",source_row,field,value))
    return tuple(out)

def import_mapped_csv(path: str | Path, mapping: Mapping[str,str]) -> ImportResult:
    normalized=_validate_mapping(mapping); trades=[]; diagnostics=[]; source_rows=0; rejected=0
    with Path(path).open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle); fieldnames=reader.fieldnames or []
        missing=[s for _,s in normalized if s not in fieldnames]
        if missing: raise ValueError(f"Missing mapped source columns: {', '.join(sorted(missing))}")
        for source_row,row in enumerate(reader,start=2):
            source_rows+=1
            row_diags=_diagnose_row(row,mapping,source_row)
            if row_diags:
                rejected+=1; diagnostics.extend(row_diags); continue
            try:
                get=lambda c: row[mapping[c]] if c in mapping else None
                stop=get("stop_loss"); qty=get("quantity")
                trades.append(Trade(symbol=(get("symbol") or "").strip(),side=(get("side") or "").strip(),entry=float(get("entry")),exit=float(get("exit")),stop_loss=float(stop) if stop not in (None,"") else None,quantity=float(qty) if qty not in (None,"") else 1.0,opened_at=datetime.fromisoformat(get("opened_at")) if get("opened_at") not in (None,"") else None,closed_at=datetime.fromisoformat(get("closed_at")) if get("closed_at") not in (None,"") else None))
            except (TypeError,ValueError,KeyError) as exc:
                rejected+=1; diagnostics.append(ImportDiagnostic("invalid_mapped_row",str(exc),source_row))
    return ImportResult(tuple(trades),tuple(diagnostics),source_rows,len(trades),rejected,normalized)
