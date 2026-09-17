# TradeGuard OSS

TradeGuard OSS is an open-source toolkit for validating trading journals, checking basic risk hygiene, and computing reproducible performance metrics from closed trades.

> Status: active early development (`v0.2.0`). The project is intended for research, education, journaling, and system-quality checks. It is not financial advice and it does not place trades.

## Why TradeGuard?

Trading journals often contain missing stop losses, inconsistent direction labels, invalid timestamps, incomplete position sizing, or performance statistics that cannot be reproduced. TradeGuard provides a small, dependency-light Python core that turns those checks into testable rules and deterministic reports.

## Current capabilities

- Versioned CSV journal schema and row-level diagnostics
- Long/short PnL calculation
- Initial risk and R-multiple calculation
- Win rate, net PnL, expectancy, gross profit/loss and profit factor
- Breakeven count and best/worst closed-trade PnL
- Closed-trade maximum drawdown
- Stop-loss and data-quality validation
- Human-readable or versioned JSON CLI output
- Deterministic JSON report export
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

Human-readable report:

```bash
tradeguard examples/sample_journal.csv
```

JSON to stdout:

```bash
tradeguard examples/sample_journal.csv --json
```

Write a deterministic, machine-readable report:

```bash
tradeguard examples/sample_journal.csv --output report.json
```

The report includes a stable top-level schema identifier (`tradeguard.report.v1`), source path, metrics, and validation issues. Metrics are skipped when validation contains errors rather than silently calculating statistics from invalid data.

## Python API

```python
from tradeguard import Trade, analyze_trades, validate_trades

trades = [
    Trade("BTCUSDT", "long", entry=60000, exit=61500, stop_loss=59000, quantity=0.1),
]

print(analyze_trades(trades))
print(validate_trades(trades))
```

## Development policy

Behavioral changes should arrive through scoped branches and pull requests with regression tests. CI runs the test suite across supported Python versions before changes are merged. Public examples must be synthetic or privacy-safe.

## Roadmap

Near-term work includes broker/export adapters, richer portfolio-risk diagnostics, report compatibility guarantees, privacy-safe sample datasets, packaging/release automation, and additional tests. See open issues for scoped work.

## Contributing

Contributions are welcome. Please read `CONTRIBUTING.md`, open an issue for material changes, and include tests for behavioral changes.

## Security and privacy

TradeGuard does not require API keys for its core journal analytics. Do not commit broker credentials, exchange keys, private trade exports, or personal financial data. See `SECURITY.md`.

## License

MIT. See `LICENSE`.
