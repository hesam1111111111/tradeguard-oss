# TradeGuard report contract v1

`tradeguard.report.v1` is the stable machine-readable report family emitted by TradeGuard OSS.

## Compatibility policy

Within v1, existing fields keep their established meaning. New capabilities may add optional fields or nested members. Consumers must ignore unknown fields. A removal, rename, type change, or semantic reinterpretation of an established field requires a new report schema identifier.

## Top-level members

- `report_schema`: always `tradeguard.report.v1`.
- `source`: input path as supplied to the CLI/API.
- `source_fingerprint`: SHA-256 of the exact input file bytes; this identifies the source artifact rather than normalized trade semantics.
- `import`: `null` for native TradeGuard CSV input, otherwise explicit mapped-import provenance.
- `journal_fingerprint`: deterministic journal integrity fingerprint.
- `metrics`: aggregate metrics, or `null` when journal validation, integrity, or import completeness blocks safe metrics.
- `issues`: validation issues retained for legacy consumers.
- `diagnostics`: structured journal diagnostics.
- `risk`: historical risk analysis, or `null` whenever metrics are suppressed.
- `segments`: segmented analytics, or `null` whenever metrics are suppressed.

## Import provenance

When the explicit mapped CSV importer is used, the additive `import` object contains:

- `mode`: `explicit_mapped_csv` for caller-supplied mappings, or `explicit_profile_csv` for an explicitly selected named profile.
- `complete`: true only when every source data row was imported without importer diagnostics.
- `source_rows`: count of source data rows processed, excluding the header.
- `imported_rows`: count converted to canonical TradeGuard `Trade` records.
- `rejected_rows`: count rejected during mapping/value conversion.
- `mapping`: exact canonical-field to source-column mapping supplied by the caller.
- `diagnostics`: deterministic source-row-indexed importer diagnostics.
- `profile`: additive profile name present only for `explicit_profile_csv`; the resolved `mapping` remains authoritative and explicit.

TradeGuard does not infer source aliases or guess ambiguous mappings. If `complete` is false, aggregate metrics, risk, and segments are suppressed rather than silently presenting analytics from a partial import. For mapped CSV imports, `source_rows = imported_rows + rejected_rows`.

## Segments

`segments.by_symbol` and `segments.by_side` are deterministic mappings whose values use the aggregate `JournalMetrics` shape.

When temporal grouping is requested, `segments.by_closed_period` is added. Its members are:

- `basis`: `recorded_closed_at_no_timezone_conversion`.
- `period`: `day` or `month`.
- `complete`: false when any supplied trade lacks a usable `closed_at` for temporal grouping.
- `measured_trades`: number of trades included in temporal segments.
- `segments`: deterministic mapping from ISO calendar key to `JournalMetrics`.
- `diagnostics`: source-indexed reasons for omitted trades.

TradeGuard does not infer or convert timezones for calendar grouping. Callers that combine multiple timezones must normalize timestamps before analysis.

## Risk semantics

Entry notional exposure and stop-based initial risk are separate concepts. Exposure is historical entry-price notional; initial risk is stop distance times quantity at entry. Neither is live mark-to-market exposure.

Missing or unusable stop data remains explicit diagnostics and is never silently interpreted as zero risk.

## Source artifact vs journal identity

`source_fingerprint` hashes exact file bytes. Byte-level changes such as BOMs or line endings intentionally change it. `journal_fingerprint` identifies canonical journal semantics after parsing/normalization. Two byte-different source files may therefore share a journal fingerprint while retaining distinct source identities. Trial Ledger evidence binds both identities.

## Determinism

Report JSON is serialized with sorted keys by the CLI. Segment producers also use deterministic key ordering. Source-index diagnostics retain input order.


## Consumer compatibility fixtures

TradeGuard treats report compatibility as an executable contract, not only a documentation promise. `tests/test_report_consumer_contract.py` builds a representative synthetic v1 report and verifies established top-level members and types, byte-stable deterministic JSON serialization, and the v1 rule that consumers ignore unknown additive members.

The fixture is generated from synthetic journal data and normalizes the source path before byte comparison so machine-specific temporary paths cannot affect the result. When an established field is removed, renamed, retyped, or reinterpreted, these tests should fail; such a change requires a new report schema identifier rather than updating the v1 expectation silently.
