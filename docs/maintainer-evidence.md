# Maintainer evidence dossier

This document provides a concise, independently inspectable record of TradeGuard OSS maintenance activity. It is intended for repository reviews and maintainer-support applications. It does not claim eligibility, acceptance, or adoption beyond observable evidence.

## What is actively maintained

TradeGuard maintenance includes:

- issue triage and scoped work definition;
- branch-based implementation through pull requests;
- regression tests for behavioral changes;
- CI across Python 3.10–3.13;
- package build and wheel smoke-install validation;
- release preparation and changelog/version synchronization;
- compatibility-contract maintenance for machine-readable report and evidence formats;
- security/privacy boundaries for examples, bug reports, and contribution workflows;
- deterministic evidence and reconciliation behavior designed to fail closed when integrity checks fail.

## Representative maintenance trail

The following merged pull requests are representative examples of the maintenance workflow:

- [#37 — deterministic journal reconciliation audit](https://github.com/hesam1111111111/tradeguard-oss/pull/37)
- [#43 — deterministic Evidence Bundle certification gate](https://github.com/hesam1111111111/tradeguard-oss/pull/43)
- [#50 — deterministic mapped-import diagnostics fix](https://github.com/hesam1111111111/tradeguard-oss/pull/50)
- [#52 — canonical normalization contract fix](https://github.com/hesam1111111111/tradeguard-oss/pull/52)
- [#67 — exact source-artifact provenance](https://github.com/hesam1111111111/tradeguard-oss/pull/67)
- [#75 — legacy Trial Ledger compatibility fix](https://github.com/hesam1111111111/tradeguard-oss/pull/75)
- [#79 — reconciliation semantic verification](https://github.com/hesam1111111111/tradeguard-oss/pull/79)
- [#81 — Trial Ledger semantic verification](https://github.com/hesam1111111111/tradeguard-oss/pull/81)
- [#85 — executable evidence compatibility contracts](https://github.com/hesam1111111111/tradeguard-oss/pull/85)
- [#87 — Evidence Bundle additive-verification fix](https://github.com/hesam1111111111/tradeguard-oss/pull/87)
- [#89 — zero-clone first-use quickstart](https://github.com/hesam1111111111/tradeguard-oss/pull/89)
- [#91 — executable end-to-end integrity demo](https://github.com/hesam1111111111/tradeguard-oss/pull/91)

These include both feature delivery and post-release defect/compatibility correction. The intent is to keep the public history reviewable rather than treating only new features as maintenance.

## Community-validation track

[#34 — Community validation: gather real-world journal import feedback](https://github.com/hesam1111111111/tradeguard-oss/issues/34) is intentionally kept open as the external validation track.

It is the place for privacy-safe, reproducible feedback about:

- CSV/export layouts;
- importer edge cases;
- validation behavior;
- report-consumer compatibility;
- documentation friction;
- concrete offline adapter/profile requests.

Credentials, private broker exports, account identifiers, and personal financial records should not be posted.

## Evidence boundaries

Repository activity demonstrates active maintenance, engineering discipline, test/release workflows, and a concrete technical problem being maintained.

It does **not** by itself establish broad adoption or ecosystem importance. External adoption evidence must come from observable signals such as genuine users, package usage/downloads, stars/forks, downstream references, external issues, or outside contributions. Such evidence should be reported only when it actually exists.

## Reviewer path

A reviewer can verify the project quickly by checking:

1. the README and end-to-end integrity demo;
2. Actions/CI history;
3. the representative PRs above;
4. versioned releases and CHANGELOG;
5. compatibility/security/contribution documentation;
6. issue #34 for genuine external validation activity.

This dossier should remain factual and should be updated when the maintenance model or evidence trail materially changes.
