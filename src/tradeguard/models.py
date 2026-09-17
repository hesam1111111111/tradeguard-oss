from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Trade:
    symbol: str
    side: str
    entry: float
    exit: float
    stop_loss: float | None = None
    quantity: float = 1.0
    opened_at: datetime | None = None
    closed_at: datetime | None = None

    @property
    def normalized_side(self) -> str:
        side = self.side.strip().lower()
        if side not in {"long", "short"}:
            raise ValueError("Side must be 'long' or 'short'.")
        return side

    @property
    def pnl(self) -> float:
        direction = 1.0 if self.normalized_side == "long" else -1.0
        return (self.exit - self.entry) * direction * self.quantity

    @property
    def initial_risk(self) -> float | None:
        if self.stop_loss is None:
            return None
        return abs(self.entry - self.stop_loss) * self.quantity

    @property
    def r_multiple(self) -> float | None:
        risk = self.initial_risk
        if risk in (None, 0):
            return None
        return self.pnl / risk
