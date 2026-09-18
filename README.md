# TradeGuard OSS

[![CI](https://github.com/hesam1111111111/tradeguard-oss/actions/workflows/ci.yml/badge.svg)](https://github.com/hesam1111111111/tradeguard-oss/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/hesam1111111111/tradeguard-oss)](https://github.com/hesam1111111111/tradeguard-oss/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10–3.13](https://img.shields.io/badge/Python-3.10%E2%80%933.13-blue.svg)](.github/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tradeguard-oss)](https://pypi.org/project/tradeguard-oss/)
## Install

```bash
pip install tradeguard-oss
```
TradeGuard OSS is an open-source toolkit for validating trading journals, checking risk hygiene, and computing reproducible performance and journal-integrity diagnostics from closed trades.

> Status: active early development (`v0.7.1`). The project is intended for research, education, journaling, and system-quality checks. It is not financial advice and it does not place trades.

## Why TradeGuard?

Trading journals often contain missing stop losses, inconsistent direction labels, invalid timestamps, duplicate records, incomplete position sizing, or performance statistics that cannot be reproduced. TradeGuard turns those checks into dependency-light, testable rules and deterministic reports.

## Current capabilities

- Versioned CSV journal schema and row-level diagnostics
- Long/short PnL, initial risk, and R-multiple calculation
- Win rate, net PnL, expectancy, gross profit/loss, profit factor, breakeven count, best/worst trade, and closed-trade maximum drawdown
- Stop-loss and data-quality validation
- Deterministic SHA-256 journal fingerprints
- Deterministic journal reconciliation with order-independent audit fingerprints, duplicate-aware deltas, and field-level drift evidence
- Exact duplicate-trade detection and blocking integrity diagnostics
- Entry-notional portfolio exposure by normalized symbol and side
- Gross/net notional exposure and configurable portfolio, symbol, and trade notional limits
- Stop-based historical risk budgets with explicit incomplete-data diagnostics
- Deterministic segmented analytics by symbol and side
- Optional deterministic closed-at grouping by calendar day or month
- Explicit mapped CSV imports with source-row provenance and rejection diagnostics
- Stable additive `tradeguard.report.v1` contract with explicit compatibility rules
- Human-readable or versioned JSON CLI output
- Deterministic JSON report export
- Automated tests across Python 3.10–3.13 plus distribution wheel smoke-install validation

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

Native TradeGuard CSV:

```bash
tradeguard examples/sample_journal.csv
tradeguard examples/sample_journal.csv --json
tradeguard examples/sample_journal.csv --output report.json
```

Explicit mapped import from a differently named CSV:

```bash
tradeguard examples/mapped_journal.csv \
  --map symbol=Ticker \
  --map side=Direction \
  --map entry=OpenPrice \
  --map exit=ClosePrice \
  --map stop_loss=Stop \
  --map quantity=Size \
  --json
```

Mappings are explicit by design. TradeGuard does not guess aliases or infer ambiguous columns. The report adds an `import` provenance section with source/imported/rejected row counts, the exact mapping, completeness, and source-indexed diagnostics. If mapped import is incomplete, metrics/risk/segments are suppressed rather than computed from a partial dataset.

Reconcile a canonical journal against another export or migration result:

```bash
tradeguard baseline.csv --reconcile-with migrated.csv --json
tradeguard baseline.csv --reconcile-with migrated.csv --output reconciliation.json --fail-on-drift
```

Reconciliation is deterministic and offline. Row order does not matter, duplicate multiplicity is preserved, and uniquely identifiable changed trades report field-level differences. The `--fail-on-drift` switch exits with status 1 when differences are found, making the command usable as a CI or migration integrity gate. Reconciliation uses a separate `tradeguard.reconciliation.v1` machine-readable envelope and does not modify the existing analytics report contract.

Add deterministic temporal analytics based on the recorded `closed_at` value:

```bash
tradeguard examples/sample_journal.csv --group-closed-by day --json
tradeguard examples/sample_journal.csv --group-closed-by month --output report.json
```

The report retains the `tradeguard.report.v1` envelope and includes source, metrics, validation issues, journal fingerprint, structured integrity diagnostics, risk analysis, segmented analytics, and optional import provenance. Metrics are skipped when blocking validation, duplicate-record errors, or incomplete mapped import make analysis unsafe.

The stable machine-readable contract and compatibility rules are documented in [`docs/report-contract-v1.md`](docs/report-contract-v1.md).

## Python API

```python
from tradeguard import (
    RiskLimits,
    Trade,
    aggregate_exposure,
    analyze_by_closed_period,
    analyze_trades,
    check_risk_limits,
    import_mapped_csv,
    journal_fingerprint,
    reconcile_journals,
    reconciliation_fingerprint,
    validate_trades,
)

trades = [Trade("BTCUSDT", "long", entry=60000, exit=61500, stop_loss=59000, quantity=0.1)]
print(validate_trades(trades))
print(journal_fingerprint(trades))
print(analyze_trades(trades))
print(analyze_by_closed_period(trades, "month"))
print(aggregate_exposure(trades))
print(check_risk_limits(trades, RiskLimits(max_gross_notional=10000)))

candidate = [Trade("BTCUSDT", "long", entry=60000, exit=61400, stop_loss=59000, quantity=0.1)]
audit = reconcile_journals(trades, candidate)
print(audit.clean, audit.mismatches)
print(reconciliation_fingerprint(trades))

mapped = import_mapped_csv(
    "examples/mapped_journal.csv",
    {"symbol": "Ticker", "side": "Direction", "entry": "OpenPrice", "exit": "ClosePrice"},
)
print(mapped.imported_rows, mapped.rejected_rows)
```

### Exposure semantics

`aggregate_exposure` and notional risk limits use absolute `entry * quantity` values from the supplied journal. They describe historical entry-notional concentration; they are **not** live positions, mark-to-market exposure, margin usage, or broker account state.

### Temporal semantics

Temporal grouping uses the recorded `closed_at` value exactly as supplied. TradeGuard does not guess or convert timezones; callers combining timestamps from different zones should normalize them before calendar grouping.

## Development policy

Behavioral changes should arrive through scoped branches and pull requests with regression tests. CI runs the test suite across supported Python versions before changes are merged. Public examples must be synthetic or privacy-safe.

## Roadmap

Near-term work includes additional offline import adapters, stronger source-data integrity diagnostics, and broader report-consumer fixtures. Live brokerage connectivity and order execution are outside the current core scope.

## Contributing

Contributions are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md), follow the [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), open an issue for material changes, and include tests for behavioral changes.

Repository-maintainer review criteria and evidence are tracked in [`docs/oss-application-readiness.md`](docs/oss-application-readiness.md).

## Security and privacy

TradeGuard does not require API keys for its core journal analytics. Do not commit broker credentials, exchange keys, private trade exports, or personal financial data. See [`SECURITY.md`](SECURITY.md).

## License

MIT. See [`LICENSE`](LICENSE).
