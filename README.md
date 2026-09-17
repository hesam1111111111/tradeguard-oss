# TradeGuard OSS

TradeGuard OSS is an open-source toolkit for validating trading journals, checking risk hygiene, and computing reproducible performance and journal-integrity diagnostics from closed trades.

> Status: active early development (`v0.5.0`). The project is intended for research, education, journaling, and system-quality checks. It is not financial advice and it does not place trades.

## Why TradeGuard?

Trading journals often contain missing stop losses, inconsistent direction labels, invalid timestamps, duplicate records, incomplete position sizing, or performance statistics that cannot be reproduced. TradeGuard turns those checks into dependency-light, testable rules and deterministic reports.

## Current capabilities

- Versioned CSV journal schema and row-level diagnostics
- Long/short PnL, initial risk, and R-multiple calculation
- Win rate, net PnL, expectancy, gross profit/loss, profit factor, breakeven count, best/worst trade, and closed-trade maximum drawdown
- Stop-loss and data-quality validation
- Deterministic SHA-256 journal fingerprints
- Exact duplicate-trade detection and blocking integrity diagnostics
- Entry-notional portfolio exposure by normalized symbol and side
- Gross/net notional exposure and configurable portfolio, symbol, and trade notional limits
- Stop-based historical risk budgets with explicit incomplete-data diagnostics
- Deterministic segmented analytics by symbol and side
- Optional deterministic closed-at grouping by calendar day or month
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

Add deterministic temporal analytics based on the recorded `closed_at` value:

```bash
tradeguard examples/sample_journal.csv --group-closed-by day --json
tradeguard examples/sample_journal.csv --group-closed-by month --output report.json
```

The report retains the `tradeguard.report.v1` envelope and includes source, metrics, validation issues, journal fingerprint, structured integrity diagnostics, risk analysis, and segmented analytics. Metrics are skipped when blocking validation or duplicate-record errors exist rather than silently calculating statistics from ambiguous data.

The stable machine-readable contract and compatibility rules are documented in [`docs/report-contract-v1.md`](docs/report-contract-v1.md).

## Python API

```python
from tradeguard import (
    RiskLimits,
    Trade,
    aggregate_exposure,
    analyze_trades,
    check_risk_limits,
    journal_fingerprint,
    validate_trades,
)

trades = [
    Trade("BTCUSDT", "long", entry=60000, exit=61500, stop_loss=59000, quantity=0.1),
]

print(validate_trades(trades))
print(journal_fingerprint(trades))
print(analyze_trades(trades))
print(aggregate_exposure(trades))
print(check_risk_limits(trades, RiskLimits(max_gross_notional=10000)))
```

### Exposure semantics

`aggregate_exposure` and notional risk limits use absolute `entry * quantity` values from the supplied journal. They describe historical entry-notional concentration; they are **not** live positions, mark-to-market exposure, margin usage, or broker account state.

## Development policy

Behavioral changes should arrive through scoped branches and pull requests with regression tests. CI runs the test suite across supported Python versions before changes are merged. Public examples must be synthetic or privacy-safe.

## Roadmap

Near-term work includes report compatibility guarantees, privacy-safe sample datasets, additional import adapters, and deeper risk diagnostics. Live brokerage connectivity and order execution are outside the current core scope.

## Contributing

Contributions are welcome. Please read `CONTRIBUTING.md`, open an issue for material changes, and include tests for behavioral changes.

## Security and privacy

TradeGuard does not require API keys for its core journal analytics. Do not commit broker credentials, exchange keys, private trade exports, or personal financial data. See `SECURITY.md`.

## License

MIT. See `LICENSE`.
