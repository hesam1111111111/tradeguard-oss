# End-to-end integrity demo

This demo shows the practical value of TradeGuard OSS with synthetic data only.

It covers:

1. deterministic journal analysis;
2. reconciliation between a reference journal and a changed candidate;
3. CI-style drift failure;
4. Trial Ledger evidence creation;
5. Evidence Bundle certification;
6. independent certification verification.

No broker connection, credentials, private trading data, or live execution are required.

## 1. Analyze the reference journal

```bash
tradeguard examples/integrity_reference.csv --json
```

The output includes deterministic analytics plus a journal fingerprint and exact source-artifact fingerprint.

## 2. Reconcile against a changed candidate

```bash
tradeguard examples/integrity_reference.csv \
  --reconcile-with examples/integrity_candidate.csv \
  --json
```

The candidate contains one intentional price change. TradeGuard should report a non-clean reconciliation with deterministic field-level drift evidence.

## 3. Use reconciliation as a CI gate

```bash
tradeguard examples/integrity_reference.csv \
  --reconcile-with examples/integrity_candidate.csv \
  --fail-on-drift
```

Because drift exists, this command must exit with status 1. That makes the workflow usable in migrations, backups, data-pipeline checks, or other automation where silent journal drift is unacceptable.

## 4. Create Trial Ledger evidence and certification

```bash
tradeguard examples/integrity_reference.csv \
  --evidence-output integrity-evidence.json \
  --certification-output integrity-certification.json \
  --run-id demo-oos-001
```

The Trial Ledger binds the analyzed journal and source identity to deterministic evidence. The certification bundle records the internal integrity result.

## 5. Verify the certification independently

```bash
tradeguard --verify-certification integrity-certification.json
```

A valid PASS bundle exits with status 0. Any post-signing tampering, malformed established fields, invalid embedded Trial Ledger evidence, or inconsistent certification semantics fails closed.

## What this demo proves

It demonstrates that TradeGuard can make local trading-journal analysis reproducible and auditable across data validation, drift detection, provenance, evidence creation, and verification.

It does **not** prove broker/exchange authenticity, real execution, trader identity, profitability, strategy quality, or future safety.
