# TradeGuard OSS

TradeGuard OSS is an open-source toolkit for validating trading journals, checking basic risk hygiene, and computing reproducible performance metrics from closed trades.

> Status: early development (`v0.1.0`). The project is intended for research, education, journaling, and system-quality checks. It is not financial advice and it does not place trades.

## Why TradeGuard?

Trading journals often contain missing stop losses, inconsistent direction labels, invalid timestamps, incomplete position sizing, or performance statistics that cannot be reproduced. TradeGuard provides a small, dependency-light Python core that turns those checks into testable rules.

## Current capabilities

- CSV journal ingestion
- Long/short PnL calculation
- Initial risk and R-multiple calculation
- Win rate, net PnL, expectancy, gross profit/loss
- Closed-trade maximum drawdown
- Stop-loss and data-quality validation
- Human-readable or JSON CLI output
- Automated tests across Python 3.10–3.13

## Install for development

```bash
git clone https://github.com/hesam1111111111/tradeguard-oss.git
cd tradeguard-oss
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .[dev]
pytest -q
```

## CSV format

Required columns:

```text
symbol,side,entry,exit
```

Optional columns:

```text
stop_loss,quantity,opened_at,closed_at
```

Example:

```csv
symbol,side,entry,exit,stop_loss,quantity,opened_at,closed_at
BTCUSDT,long,60000,61500,59000,0.1,2026-01-01T10:00:00,2026-01-01T13:00:00
ETHUSDT,short,3200,3100,3260,1.0,2026-01-02T09:00:00,2026-01-02T12:00:00
```

## CLI

```bash
tradeguard examples/sample_journal.csv
tradeguard examples/sample_journal.csv --json
```

## Python API

```python
from tradeguard import Trade, analyze_trades, validate_trades

trades = [
    Trade("BTCUSDT", "long", entry=60000, exit=61500, stop_loss=59000, quantity=0.1),
]

print(analyze_trades(trades))
print(validate_trades(trades))
```

## Roadmap

Near-term work includes schema versioning, richer journal diagnostics, broker/export adapters, deterministic report export, additional risk metrics, and privacy-safe sample datasets. See open issues for scoped work.

## Contributing

Contributions are welcome. Please read `CONTRIBUTING.md`, open an issue for material changes, and include tests for behavioral changes.

## Security and privacy

TradeGuard does not require API keys for its core journal analytics. Do not commit broker credentials, exchange keys, private trade exports, or personal financial data. See `SECURITY.md`.

## License

MIT. See `LICENSE`.
