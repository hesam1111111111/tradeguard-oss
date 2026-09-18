from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .importers import ImportResult, import_mapped_csv

_PROFILE_DATA: dict[str, dict[str, str]] = {
    "generic_ohlc": {
        "symbol": "Symbol",
        "side": "Side",
        "entry": "Entry",
        "exit": "Exit",
        "stop_loss": "StopLoss",
        "quantity": "Quantity",
        "opened_at": "OpenedAt",
        "closed_at": "ClosedAt",
    },
    "generic_ticket_export": {
        "symbol": "Ticker",
        "side": "Direction",
        "entry": "OpenPrice",
        "exit": "ClosePrice",
        "stop_loss": "Stop",
        "quantity": "Size",
        "opened_at": "OpenTime",
        "closed_at": "CloseTime",
    },
}

IMPORT_PROFILES: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {name: MappingProxyType(mapping) for name, mapping in sorted(_PROFILE_DATA.items())}
)


def available_import_profiles() -> tuple[str, ...]:
    return tuple(IMPORT_PROFILES)


def get_import_profile(name: str) -> Mapping[str, str]:
    try:
        return IMPORT_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown import profile: {name}") from exc


def import_csv_with_profile(path: str, profile: str) -> ImportResult:
    return import_mapped_csv(path, get_import_profile(profile))
