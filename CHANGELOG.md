# Changelog

All notable changes to TradeGuard OSS are documented in this file.

The project follows semantic versioning while the public API is still evolving.

## [Unreleased]

## [0.3.0] - 2026-09-17

### Added
- Deterministic SHA-256 journal fingerprinting using canonical trade records.
- Exact duplicate-trade detection with first and duplicate source indices.
- Structured machine-readable journal diagnostics and integrity status.
- Entry-notional portfolio exposure aggregation by normalized symbol and side.
- Gross and net notional exposure calculations.
- Configurable portfolio, per-symbol, and per-trade notional risk limits with structured breaches.
- Regression tests for journal integrity, diagnostics, exposure aggregation, and risk-limit boundaries.

### Changed
- JSON reports include additive integrity diagnostics while retaining the `tradeguard.report.v1` compatibility envelope.
- Metrics are suppressed when blocking validation or duplicate-trade integrity errors exist.
- Human-readable reports handle undefined profit factor without formatting failures.
- Public package exports include the v0.3.0 portfolio-risk API.

### Scope
- Portfolio exposure in v0.3.0 is historical entry-price notional over the supplied journal, not live mark-to-market exposure.
- TradeGuard remains an analytics, validation, and risk-analysis toolkit; it does not connect to brokers or execute orders.

## [0.2.0] - 2026-09-17

### Added
- Versioned journal schema contract and row-level CSV diagnostics.
- Profit factor, breakeven count, best trade, and worst trade metrics.
- Stable `tradeguard.report.v1` JSON report envelope.
- Deterministic report-file export through the CLI `--output` option.
- Regression tests for report generation and expanded risk metrics.

### Changed
- CLI validates journals before computing metrics and suppresses misleading metrics when validation errors exist.
- Directional calculations reject unsupported trade sides instead of treating them as short positions.
- CI verifies supported Python versions 3.10 through 3.13.

## [0.1.0] - 2026-09-17

### Added
- Initial Python package structure.
- CSV journal ingestion.
- Trade PnL, initial risk, and R-multiple calculations.
- Journal metrics including win rate, expectancy, and closed-trade maximum drawdown.
- Validation rules for symbol, side, prices, quantity, stop loss, and timestamp ordering.
- CLI with text and JSON output.
- Pytest coverage and GitHub Actions CI.
- Public contribution, security, and sample-data documentation.
