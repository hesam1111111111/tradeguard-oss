# Trial Ledger v1

`tradeguard.trial-ledger.v1` is a deterministic local evidence contract for a completed TradeGuard journal analysis.

It preserves reproducible evidence about a run without claiming broker verification, identity attestation, or live execution provenance.

## Compatibility policy

Within v1, established members retain their meaning and type. New optional members may be added. Consumers should ignore unknown members. Removing, renaming, retyping, or semantically reinterpreting an established member requires a new Trial Ledger schema identifier.

## Established members

- `trial_ledger_schema`: always `tradeguard.trial-ledger.v1`.
- `run_id`: caller-supplied non-blank run identifier.
- `parent_evidence_fingerprint`: optional prior Trial Ledger SHA-256 link, otherwise `null`.
- `source_fingerprint`: exact source-artifact SHA-256, or `null` for supported legacy report producers that predate this additive provenance field.
- `journal_fingerprint`: canonical journal SHA-256 identity.
- `record_count`: non-negative analyzed trade count.
- `configuration`: caller-controlled analysis configuration object.
- `import`: mapped-import provenance object or `null`.
- `metrics`: deterministic journal metrics object.
- `diagnostics`: structured journal diagnostics object.
- `risk`: risk-analysis object or `null`.
- `segments`: segmented analytics object or `null`.
- `evidence_fingerprint`: SHA-256 integrity fingerprint over the complete evidence record except this member itself.

## Semantic invariants

`validate_trial_evidence()` fails closed unless the v1 structure is internally consistent. Current checks include:

- non-blank `run_id`;
- valid SHA-256 syntax for journal, source, and parent fingerprints when present;
- non-negative `record_count`;
- `metrics.trades == record_count`;
- required object/list shapes;
- mapped-import accounting `source_rows = imported_rows + rejected_rows`;
- mapped-import `complete` agrees with whether rejected rows are zero;
- import-level source fingerprint agrees with the top-level source fingerprint.

## Determinism

The evidence fingerprint is SHA-256 over canonical JSON for the complete evidence record except the fingerprint itself. Object keys are sorted and compact JSON separators are used. Wall-clock timestamps are deliberately excluded, so equivalent semantic inputs and configuration produce the same fingerprint.

TradeGuard does not invent whether a run was a backtest, OOS test, demo, or live run. Such semantics belong in explicit caller-controlled configuration.

## Fail-closed behavior

Evidence is produced only from a valid `tradeguard.report.v1` report with metrics available. Journals blocked by validation, duplicate integrity errors, or incomplete mapped import cannot be turned into Trial Ledger evidence.

Creation also validates the resulting Trial Ledger v1 record before fingerprinting it.

## Chain linkage

An evidence record may contain `parent_evidence_fingerprint`, a 64-character SHA-256 digest of a prior evidence record. This creates an explicit local chain such as backtest -> OOS -> demo. It does not prove who created either record or that a broker supplied the data.

`verify_trial_evidence()` validates the semantic contract, recomputes the fingerprint, and can require an expected parent fingerprint.

## CLI

```bash
tradeguard journal.csv --evidence-output evidence.json --run-id oos-0042
tradeguard journal.csv --evidence-output demo.json --run-id demo-0001 \
  --parent-evidence-fingerprint <64-char-sha256>
```

Risk limits, risk budgets, temporal grouping, and explicit import mappings used by the CLI are captured in the evidence configuration.

## Consumer compatibility fixtures

`tests/test_evidence_consumer_contract.py` protects the established v1 member/type contract, deterministic serialization, semantic verification, legacy `source_fingerprint: null` support, and additive-member tolerance for consumers.

A breaking v1 change should fail these tests and requires a new schema identifier rather than silently rewriting the fixture.

## Privacy and scope

Evidence can contain derived journal metrics, diagnostics, risk results, segments, and import provenance. Treat evidence as potentially sensitive trading data.

Verification proves deterministic internal integrity and contract consistency only. It does not prove broker/exchange provenance, identity, real execution, profitability, strategy quality, or future safety.
