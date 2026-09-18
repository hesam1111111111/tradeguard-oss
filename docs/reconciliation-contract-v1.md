# Reconciliation contract v1

`tradeguard.reconciliation.v1` is TradeGuard's deterministic machine-readable contract for comparing two canonical journals and preserving reproducible drift evidence.

## Compatibility policy

Within v1, established members retain their meaning and type. New optional members may be added. Consumers should ignore unknown members. Removing, renaming, retyping, or semantically reinterpreting an established member requires a new reconciliation schema identifier.

## Established members

- `reconciliation_schema`: always `tradeguard.reconciliation.v1`.
- `reference` and `candidate`: input paths as supplied by the caller.
- `reference_source_fingerprint` and `candidate_source_fingerprint`: SHA-256 of the exact source file bytes.
- `clean`: true only when no missing, unexpected, or mismatched evidence remains.
- `reference_fingerprint` and `candidate_fingerprint`: order-independent semantic journal fingerprints.
- `reference_rows`, `candidate_rows`, `exact_matches`, and `modified_rows`: non-negative accounting integers.
- `missing` and `unexpected`: deterministic record-delta lists with positive counts.
- `mismatches`: deterministic field-level differences for uniquely pairable modified rows.
- `reconciliation_evidence_fingerprint`: SHA-256 integrity fingerprint over the complete envelope except this member itself.

## Accounting invariants

The v1 semantic validator requires:

- `reference_rows = exact_matches + modified_rows + sum(missing.count)`;
- `candidate_rows = exact_matches + modified_rows + sum(unexpected.count)`;
- `modified_rows` equals the number of distinct mismatch identities;
- `clean` is true exactly when `missing`, `unexpected`, and `mismatches` are all empty;
- digest fields are 64-character SHA-256 hexadecimal strings;
- row/count members are non-negative integers and delta counts are positive.

## Source-artifact identity vs semantic identity

Source fingerprints identify exact file bytes. Byte-only differences such as line endings can therefore produce different source fingerprints even when canonical trade semantics are equal.

Journal fingerprints identify normalized journal semantics and intentionally ignore row order.

## Determinism and verification

Reconciliation evidence is signed with canonical JSON using sorted keys, compact separators, UTF-8, and no NaN values. Equivalent semantic envelopes therefore produce the same evidence fingerprint.

`verify_reconciliation_evidence()` fails closed unless both the v1 semantic contract and the stored evidence fingerprint verify.

CLI verification requires no CSV inputs:

```bash
tradeguard --verify-reconciliation reconciliation.json
```

Exit status is 0 for valid evidence and 1 for invalid evidence.

## Consumer compatibility fixtures

`tests/test_evidence_consumer_contract.py` protects established v1 top-level members/types, deterministic serialization, and additive-member tolerance for downstream consumers.

A change that removes, renames, retypes, or reinterprets an established v1 member should fail these tests and requires a new schema identifier rather than silently updating the fixture.

## Scope

Reconciliation proves deterministic internal integrity and contract consistency only. It does not attest broker/exchange provenance, real execution, profitability, strategy quality, identity, or future safety.
