# Evidence Bundle v1

`tradeguard.evidence-bundle.v1` is TradeGuard's deterministic offline certification envelope for `tradeguard.trial-ledger.v1` evidence.

A `PASS` means only that the supplied evidence passed the documented internal integrity and semantic-contract checks. It does **not** prove broker/exchange provenance, real execution, identity, profitability, strategy quality, or future safety.

## Compatibility policy

Within v1, established members retain their meaning and type. New optional members may be added. Consumers should ignore unknown members. Removing, renaming, retyping, or semantically reinterpreting an established member requires a new Evidence Bundle schema identifier.

## Established members

- `evidence_bundle_schema`: always `tradeguard.evidence-bundle.v1`.
- `certification`: object containing `status`, deterministic `checks`, and the declared verification `scope`.
- `expected_parent_fingerprint`: optional expected Trial Ledger parent SHA-256, otherwise `null`.
- `evidence`: embedded `tradeguard.trial-ledger.v1` evidence object.
- `bundle_fingerprint`: SHA-256 integrity fingerprint over the complete bundle except this member itself.

## Deterministic contract

The bundle fingerprint is computed from canonical JSON with sorted keys and no timestamps. Equivalent semantic evidence and verification requirements therefore produce the same bundle and fingerprint.

## Certification gate

Current v1 checks are intentionally narrow and fail closed:

- the embedded Trial Ledger evidence must pass both semantic validation and fingerprint verification;
- when an expected parent fingerprint is supplied, the stored parent link must match it.

All required checks must pass for `certification.status` to be `PASS`. Otherwise it is `FAIL`. There are no heuristic scores and no profitability threshold.

`validate_evidence_bundle()` validates the established v1 members and independently recomputes the documented certification semantics. `verify_evidence_bundle()` then verifies the stored fingerprint over the actual supplied unsigned bundle, including unknown additive members. Signed additive members are therefore compatible, while malformed established members, inconsistent certification semantics, or any post-signing tampering fail closed.

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

Verify a stored certification bundle. No CSV input is required:

```bash
tradeguard --verify-certification certification.json
```

The CLI gate exits with status 0 only when the bundle is internally valid **and** certification status is `PASS`; otherwise it exits with status 1.

## Consumer compatibility fixtures

`tests/test_evidence_consumer_contract.py` protects the established v1 top-level members/types, deterministic serialization, PASS/FAIL contract shape, and additive-member tolerance for consumers.

Breaking established v1 semantics requires a new schema identifier rather than silently changing the fixture.

## Security and privacy

The verifier is local and requires no credentials or remote service. Evidence may contain sensitive derived trading information. Do not commit private journals, account identifiers, API keys, broker credentials, or personal financial exports to public repositories.
