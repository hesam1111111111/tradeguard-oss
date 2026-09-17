from __future__ import annotations

SCHEMA_VERSION = "1.0"
REQUIRED_COLUMNS = ("symbol", "side", "entry", "exit")
OPTIONAL_COLUMNS = ("stop_loss", "quantity", "opened_at", "closed_at")


def validate_columns(columns: list[str] | tuple[str, ...]) -> list[str]:
    """Return required journal columns that are missing from an input header."""
    present = {column.strip() for column in columns}
    return [column for column in REQUIRED_COLUMNS if column not in present]
