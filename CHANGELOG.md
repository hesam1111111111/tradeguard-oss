# Changelog

All notable changes to TradeGuard OSS are documented in this file.

The project follows semantic versioning while the public API is still evolving.

## [Unreleased]

### Added
- Reconciliation evidence verification now validates required v1 structure, SHA-256 digest syntax, non-negative accounting fields, delta/mismatch shapes, and core internal invariants before accepting a fingerprint.
- Public `validate_reconciliation_evidence()` API for deterministic contract checks.

### Changed
- Reconciliation signing now fails closed for malformed or logically contradictory envelopes instead of fingerprinting them.

## [0.14.0] - 2026-09-18

### Added
- Exact SHA-256 source-artifact identities for both reference and candidate inputs in `tradeguard.reconciliation.v1`.
- Deterministic `reconciliation_evidence_fingerprint` sealing for saved reconciliation envelopes.
- Public reconciliation evidence signing and verification APIs.
- Fail-closed `--verify-reconciliation` CLI verification that requires no CSV inputs.
- Regression coverage proving semantically equivalent but byte-different journals can reconcile cleanly while retaining distinct source-artifact provenance.

### Fixed
- Trial Ledger evidence creation accepts otherwise-valid legacy `tradeguard.report.v1` producers that predate the additive `source_fingerprint` member; unavailable source-artifact provenance is represented as `null`, never fabricated.
- Present `source_fingerprint` values remain strictly validated and bound into deterministic evidence.

### Compatibility
- Existing reconciliation semantics remain unchanged; source-artifact identities and envelope integrity fingerprints are additive members of `tradeguard.reconciliation.v1`.
- Existing report, Trial Ledger, and Evidence Bundle schema identifiers remain unchanged.
- Legacy report.v1 producers remain accepted at the Trial Ledger API boundary when source-artifact provenance is unavailable.

### Scope
- Verification certifies internal deterministic reconciliation-envelope integrity only; it does not attest broker/exchange provenance, real execution, profitability, strategy quality, identity, or future safety.
- No broker connectivity, credentials, market-data enrichment, signals, strategy logic, or order execution are introduced.

## [0.13.0] - 2026-09-18

### Added
- Explicit `--import-profile` CLI selection for reusable CSV import profiles, including read-only import preview support.
- Deterministic CLI profile introspection with `--list-import-profiles` and `--describe-import-profile`, including machine-readable JSON output.
- Exact SHA-256 `source_fingerprint` for input artifact bytes in `tradeguard.report.v1`.
- Trial Ledger binding to both exact source-artifact identity and canonical journal identity.
- Regression coverage proving byte-different but semantically equivalent CSV files retain distinct source provenance.

### Changed
- Profile-based import provenance records the selected profile and resolved explicit mapping.
- Trial Ledger configuration records explicit profile selection.
- Report contract documentation distinguishes source-artifact identity from canonical journal semantics.

### Compatibility
- Existing `--map` behavior remains supported and mutually exclusive with `--import-profile`.
- `source_fingerprint` is an additive `tradeguard.report.v1` member; existing schema identifiers and established field semantics are preserved.
- No changes to `tradeguard.reconciliation.v1`, `tradeguard.trial-ledger.v1`, or `tradeguard.evidence-bundle.v1` schema identifiers.
- No live broker connectivity, credentials, strategy logic, signals, or order execution are introduced.


## [0.12.0] - 2026-09-18

### Added
- Fail-closed mapped CSV source-structure checks for duplicate headers and unexpected extra row values.
- Explicit immutable reusable CSV import profiles with public listing, selection, and profile-import APIs.
- Synthetic adapter fixtures proving profile imports match equivalent canonical TradeGuard CSV.
- Executable `tradeguard.report.v1` consumer compatibility tests covering established top-level members/types, deterministic byte-stable JSON serialization, and additive unknown-field tolerance.

### Changed
- README and contract documentation now describe source-integrity checks, explicit adapter-profile extension rules, and executable consumer compatibility guarantees.

### Compatibility
- Existing explicit `--map` behavior remains supported.
- No changes to `tradeguard.report.v1`, `tradeguard.reconciliation.v1`, `tradeguard.trial-ledger.v1`, or `tradeguard.evidence-bundle.v1` schema identifiers or established semantics.
- No live broker connectivity, credentials, strategy logic, signals, or order execution are introduced.


## [0.11.1] - 2026-09-18

### Fixed
- Mapped CSV diagnostics now use explicit canonical field ordering instead of unordered sets, preserving deterministic output across processes and supported Python versions.
- Whitespace-only mapped numeric and datetime values are handled consistently as blank values, avoiding duplicate or misleading diagnostics.
- Canonical trade validation now normalizes side values with the same `strip().lower()` contract used by trade normalization and fingerprints.
- Canonical CSV headers are normalized before row access, preventing schema/loader disagreement for surrounding whitespace.
- CSV headers that collide after whitespace normalization now fail explicitly instead of being interpreted ambiguously.

### Compatibility
- No report, reconciliation, Trial Ledger, Evidence Bundle, or diagnostic-code schema changes.
- This is a backward-compatible patch release.

## [0.11.0] - 2026-09-18\n\n### Added\n- Deterministic field-level mapped CSV diagnostics with stable codes for missing required values, invalid numbers, and invalid datetimes.\n- Read-only `--import-preview` workflow reporting source, importable, and rejected row counts without running analytics.\n- Canonical field, source row, and offending-value evidence for mapped-import failures.\n\n### Fixed\n- `--verify-certification` is now a fail-closed CLI gate: exit 0 requires both a valid bundle and certification status `PASS`.\n- Certification verification no longer requires an unrelated positional CSV path.\n- Non-object certification JSON fails closed instead of reaching object-only verification logic.\n\n### Compatibility\n- `tradeguard.report.v1`, `tradeguard.reconciliation.v1`, `tradeguard.trial-ledger.v1`, and `tradeguard.evidence-bundle.v1` remain backward compatible.\n- `verify_evidence_bundle()` retains integrity/consistency semantics; the stricter PASS requirement applies to the CLI certification gate.\n\n### Scope\n- Import preview and certification verification remain local/offline and do not require broker credentials, live connectivity, signals, or order execution.\n

## [0.10.0] - 2026-09-18

### Added
- Versioned `tradeguard.evidence-bundle.v1` deterministic offline certification contract.
- Public `build_evidence_bundle` and `verify_evidence_bundle` APIs.
- Explicit `PASS` / `FAIL` certification derived only from documented machine-checkable integrity checks.
- Trial Ledger tamper verification and optional expected-parent chain validation.
- Deterministic SHA-256 bundle fingerprints and independent bundle re-verification.
- CLI certification export with `--certification-output` and CI-friendly verification with `--verify-certification`.
- Regression coverage for determinism, evidence tampering, bundle tampering, parent mismatch, and CLI verification.
- Formal Evidence Bundle v1 contract documentation.

### Compatibility
- `tradeguard.report.v1`, `tradeguard.reconciliation.v1`, and `tradeguard.trial-ledger.v1` remain additive and backward compatible.
- Certification verifies internal evidence integrity only; it does not attest broker/exchange provenance, real execution, identity, profitability, strategy quality, or future safety.

### Scope
- Verification is local/offline and requires no credentials, remote service, brokerage connection, signals, or order execution.


## [0.9.0] - 2026-09-18

### Added
- Versioned `tradeguard.trial-ledger.v1` deterministic evidence contract.
- Explicit caller-owned run identifiers and optional parent evidence fingerprint linkage.
- SHA-256 evidence fingerprints and local tamper verification through the public API.
- Fail-closed evidence creation when journal validation, duplicate integrity, or mapped-import completeness makes analysis unsafe.
- CLI evidence export with `--evidence-output`, `--run-id`, and optional `--parent-evidence-fingerprint`.
- Evidence capture of analysis configuration, derived metrics, diagnostics, risk results, segments, and import provenance.
- Contract documentation and regression coverage for determinism, material drift, chain verification, tampering, invalid input, and CLI behavior.

### Compatibility
- `tradeguard.report.v1` and `tradeguard.reconciliation.v1` remain unchanged.
- Trial Ledger is an additive local evidence layer and does not claim broker verification, identity attestation, or live execution provenance.

### Scope
- No broker credentials, remote service, live synchronization, signals, or order execution are required or included.


## [0.8.0] - 2026-09-18

### Added
- Deterministic offline journal reconciliation through the public `reconcile_journals` API.
- Order-independent SHA-256 reconciliation fingerprints for audit and migration verification.
- Duplicate-aware missing and unexpected record deltas that preserve multiplicity.
- Field-level mismatch evidence for uniquely pairable changed trades.
- Versioned `tradeguard.reconciliation.v1` machine-readable audit output.
- CLI reconciliation with `--reconcile-with`.
- CI/migration integrity gating with `--fail-on-drift`, which exits with status 1 when drift is detected.
- Regression coverage for reordered journals, duplicate multiplicity, field drift, ambiguous identities, CLI JSON output, and CI-friendly failure semantics.

### Changed
- README now documents reconciliation as an integrity primitive for export, migration, backup, and downstream journal verification.
- Existing `tradeguard.report.v1` analytics behavior remains unchanged.

### Compatibility
- `tradeguard.reconciliation.v1` is a separate additive contract and does not alter `tradeguard.report.v1`.
- Reconciliation is deterministic and intentionally avoids fuzzy or heuristic matching.

### Scope
- Reconciliation operates on local canonical TradeGuard CSV journals only.
- No broker credentials, live synchronization, market-data enrichment, strategy inference, or order execution are included.

## [0.7.1] - 2026-09-17

### Changed
- Added PyPI project metadata links for Homepage, Repository, Issues, and Changelog.
- Added PyPI install guidance and version badge to the README.
- Synchronized package and runtime version metadata for the patch release.
- Added Trusted Publisher-based PyPI release automation.


## [0.7.0] - 2026-09-17

### Added
- Deterministic generic CSV importing through explicit canonical-to-source column mappings.
- Public importer API: `ImportDiagnostic`, `ImportResult`, and `import_mapped_csv`.
- Source-indexed import diagnostics with source/imported/rejected row accounting.
- Repeatable CLI `--map canonical=source_column` controls for mapped imports.
- Additive `import` provenance in `tradeguard.report.v1`, including mapping, completeness, row counts, and diagnostics.
- Privacy-safe synthetic mapped-import examples and regression coverage.

### Changed
- Incomplete mapped imports suppress metrics, risk, and segmented analytics rather than analyzing a partial dataset as complete.
- Native TradeGuard CSV behavior remains backward compatible and reports `import: null`.
- Report-contract regression coverage now treats import provenance as an additive v1 field.

### Compatibility
- `tradeguard.report.v1` remains the schema identifier; import provenance is additive.
- Mapping is explicit only. TradeGuard does not guess aliases or silently infer ambiguous source fields.

### Scope
- Import adapters operate on local historical files only.
- No broker/exchange connectivity, credentials, live synchronization, signals, or order execution are included.

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
