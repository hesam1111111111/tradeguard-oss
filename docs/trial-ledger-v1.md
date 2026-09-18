# Trial Ledger v1

`tradeguard.trial-ledger.v1` is a deterministic local evidence contract for a completed TradeGuard journal analysis.

It is designed to preserve reproducible evidence about a run without claiming broker verification, identity attestation, or live execution provenance.

## Determinism

The evidence fingerprint is SHA-256 over canonical JSON for the complete evidence record except the fingerprint itself. Object keys are sorted and compact JSON separators are used. Wall-clock timestamps are deliberately excluded, so equivalent semantic inputs and configuration produce the same fingerprint.

The caller must provide a non-blank `run_id`. TradeGuard does not invent whether a run was a backtest, OOS test, demo, or live run. Such semantics belong in explicit caller-controlled configuration.

## Fail-closed behavior

Evidence is produced only from a valid `tradeguard.report.v1` report with metrics available. Journals blocked by validation, duplicate integrity errors, or incomplete mapped import cannot be turned into trial evidence.

## Chain linkage

An evidence record may contain `parent_evidence_fingerprint`, a 64-character SHA-256 digest of a prior evidence record. This creates an explicit local chain such as backtest -> OOS -> demo. It does not prove who created either record or that a broker supplied the data.

`verify_trial_evidence` recomputes the fingerprint and can also require an expected parent fingerprint. Any material change to the stored evidence invalidates verification.

## CLI

```bash
tradeguard journal.csv --evidence-output evidence.json --run-id oos-0042
tradeguard journal.csv --evidence-output demo.json --run-id demo-0001 \
  --parent-evidence-fingerprint <64-char-sha256>
```

Risk limits, risk budgets, temporal grouping, and explicit import mappings used by the CLI are captured in the evidence configuration.

## Privacy

Evidence can contain derived journal metrics, diagnostics, risk results, segments, and import provenance. Treat evidence bundles as potentially sensitive trading records. Do not place private exports, account identifiers, API keys, broker credentials, or unnecessary personal data in public repositories.
