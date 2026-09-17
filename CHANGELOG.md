# Changelog

All notable changes to TradeGuard OSS are documented in this file.

The project follows semantic versioning while the public API is still evolving.

## [Unreleased]

## [0.6.0] - 2026-09-17

### Added
- Deterministic temporal analytics grouped by recorded `closed_at` calendar day or month.
- Explicit `missing_closed_at` diagnostics and measured-trade counts for incomplete temporal coverage.
- Additive temporal report output under `segments.by_closed_period` in `tradeguard.report.v1`.
- CLI temporal grouping through `--group-closed-by day|month`.
- Formal `tradeguard.report.v1` compatibility documentation covering additive fields, nullability, deterministic ordering, and timezone semantics.
- Dedicated report-contract regression tests ensuring temporal analytics do not mutate established v1 metrics, risk, symbol, or side sections.
- Public temporal-analysis API exports: `TemporalAnalysis`, `TemporalDiagnostic`, and `analyze_by_closed_period`.

### Compatibility
- `tradeguard.report.v1` remains the report schema identifier.
- Temporal report data is strictly additive and is omitted unless explicitly requested.
- Existing invalid-journal behavior remains unchanged: unsafe metrics, risk, and segments are suppressed rather than fabricated.

### Scope
- Temporal grouping uses recorded `closed_at` values exactly as supplied and does not infer or convert timezones.
- TradeGuard remains historical journal analytics only; no broker connectivity, credentials, live mark-to-market state, or order execution are included.

## [0.5.0] - 2026-09-17

### Added
- Validated stop-based `RiskBudget` configuration for per-trade and aggregate journal risk budgets.
- Structured deterministic risk-budget breaches and explicit diagnostics for trades whose stop-based initial risk cannot be measured.
- Deterministic segmented analytics by normalized symbol and side.
- Additive machine-readable risk-budget and segmented-analytics output in `tradeguard.report.v1`.
- CLI flags `--max-trade-initial-risk` and `--max-total-initial-risk`.
- Distribution build and isolated wheel smoke-install validation in CI.

### Changed
- CLI risk-limit inputs reject zero, negative, NaN, and infinite values cleanly.
- Missing or unusable stop data never silently becomes zero risk; incomplete aggregate risk-budget evaluation remains explicit.
- Public package exports include the v0.5.0 risk-budget and segmentation APIs.

### Compatibility
- `tradeguard.report.v1` remains stable; v0.5 fields are additive.
- Historical entry-notional exposure remains separate from stop-based initial risk.

### Scope
- TradeGuard remains an analytics, validation, and historical risk-analysis toolkit; it does not connect to brokers or execute orders.

## [0.4.0] - 2026-09-17

### Added
- Positive, finite validation for configured notional limits and direct risk API inputs.
- Explicit stop-based initial-risk analysis, kept distinct from notional exposure.
- Structured diagnostics for trades whose initial risk cannot be measured.
- Additive machine-readable `risk` section in `tradeguard.report.v1` reports.
- Historical entry-notional exposure details and deterministic risk-limit breaches in JSON reports.
- CLI flags for portfolio, symbol, and per-trade notional limits.
- Regression coverage for invalid numeric inputs, initial-risk semantics, report compatibility, deterministic export, and CLI limits.

### Changed
- Direct risk APIs no longer hide invalid entry or quantity values through absolute-value normalization.
- Blank symbols and invalid sides fail explicitly during exposure aggregation.
- Risk reporting is suppressed with metrics when blocking journal integrity or validation errors are present.
- Public package exports include the v0.4.0 initial-risk API.

### Compatibility
- The report identifier remains `tradeguard.report.v1`; the new top-level `risk` member is additive and existing top-level fields are retained.

### Scope
- Notional exposure is historical entry-price notional, not live mark-to-market exposure.
- Initial risk is stop-based risk at entry and is never conflated with notional exposure.
- TradeGuard remains an analytics, validation, and risk-analysis toolkit; it does not connect to brokers or execute orders.

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
