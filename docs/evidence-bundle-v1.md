# Evidence Bundle v1

`tradeguard.evidence-bundle.v1` is TradeGuard's deterministic offline certification envelope for `tradeguard.trial-ledger.v1` evidence.

A `PASS` means only that the supplied evidence passed the documented internal integrity checks. It does **not** prove broker/exchange provenance, real execution, identity, profitability, strategy quality, or future safety.

## Deterministic contract

The bundle contains the Trial Ledger evidence, the optional expected parent fingerprint, explicit machine-check results, a certification status, and a SHA-256 `bundle_fingerprint`. The fingerprint is computed from canonical JSON with sorted keys and no timestamps.

Equivalent semantic evidence and verification requirements therefore produce the same bundle and fingerprint.

## Certification gate

Current v1 checks are intentionally narrow and fail closed:

- the embedded Trial Ledger evidence must pass its own fingerprint verification;
- when an expected parent fingerprint is supplied, the stored parent link must match it.

All required checks must pass for `certification.status` to be `PASS`. Otherwise it is `FAIL`. There are no heuristic scores and no profitability threshold.

`verify_evidence_bundle` verifies the bundle fingerprint and independently rebuilds the deterministic certification result. A modified bundle or modified embedded evidence fails verification unless a new bundle is explicitly built; rebuilding does not convert invalid Trial Ledger evidence into a PASS.

## CLI

Create Trial Ledger evidence and its certification bundle:

```bash
tradeguard journal.csv --evidence-output evidence.json --certification-output certification.json --run-id oos-0042
```

For a linked run:

```bash
tradeguard journal.csv --evidence-output demo.json --certification-output demo-cert.json \
  --run-id demo-0001 --parent-evidence-fingerprint <64-char-sha256>
```

Verify a stored certification bundle:

```bash
tradeguard journal.csv --verify-certification certification.json
```

Verification exits with status 0 when the bundle is valid and status 1 when it is invalid, making the command suitable for CI gates.

## Security and privacy

The verifier is local and requires no credentials or remote service. Evidence may contain sensitive derived trading information. Do not commit private journals, account identifiers, API keys, broker credentials, or personal financial exports to public repositories.
