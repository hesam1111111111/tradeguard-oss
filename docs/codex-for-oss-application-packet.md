# Codex for Open Source application packet

This packet is a factual source-of-truth for preparing a Codex for Open Source application for TradeGuard OSS.

OpenAI's current program says it considers active open-source projects with meaningful usage, broad adoption, or clear importance to the software ecosystem, and reviews evidence such as repository usage, ecosystem importance, pull-request review, issue triage, release management, and other ongoing maintainer responsibilities.

## Repository facts

- Repository: https://github.com/hesam1111111111/tradeguard-oss
- Visibility: public
- License: MIT
- Package: `tradeguard-oss`
- Distribution: PyPI
- Supported Python versions in CI: 3.10–3.13
- Scope: deterministic validation, risk/performance analysis, reconciliation, provenance, Trial Ledger evidence, certification, and compatibility contracts for local trading-journal workflows
- Explicit non-scope: broker connectivity, credentials, live execution, identity attestation, profitability claims

## Maintainer role

Primary maintainer.

Ongoing responsibilities include issue triage, scoped implementation, regression testing, CI maintenance, release preparation, compatibility guarantees, security/privacy boundaries, documentation, and post-release defect correction.

See: [Maintainer evidence dossier](maintainer-evidence.md)

## Why this repository may qualify

TradeGuard OSS maintains deterministic audit and integrity tooling for trading-journal data: validation, reproducible analytics, reconciliation, exact source provenance, tamper-verifiable evidence, fail-closed certification, and compatibility contracts. The repository demonstrates active issue/PR triage, multi-version CI, release management, regression fixes, and ongoing maintenance.

This statement intentionally does not claim broad adoption unless external evidence exists.

## Draft: "Why does this repository qualify?"

> TradeGuard OSS is an actively maintained Python toolkit for deterministic trading-journal validation, reconciliation, provenance, and tamper-verifiable evidence. It has public releases, PyPI distribution, Python 3.10–3.13 CI, regression testing, issue/PR triage, compatibility contracts, and documented release/security workflows. Its goal is reproducible auditability for local trading-data pipelines.

Keep this answer under the form's current 500-character limit when submitting.

## Draft: maintainer role

> Primary maintainer responsible for issue triage, scoped PRs, regression testing, CI, release management, compatibility contracts, security/privacy boundaries, documentation, and post-release maintenance.

## Draft: API credit use

> Use API credits for OSS maintenance automation: PR review assistance, issue triage, regression-test generation, release-note/changelog checks, compatibility review, security-oriented code inspection, and maintenance of deterministic evidence/integrity workflows. Human review remains the final gate for merges and releases.

Keep this answer under the form's current 500-character limit when submitting.

## Draft: anything else

> TradeGuard deliberately avoids unsupported claims: it does not place trades or attest broker execution, identity, or profitability. Public examples are synthetic/privacy-safe. The repository includes an executable end-to-end integrity demo and a maintainer evidence dossier so reviewers can inspect its workflows quickly.

Keep this answer under the form's current 500-character limit when submitting.

## External adoption evidence

A dated factual snapshot is maintained in [`docs/external-evidence-snapshot.md`](external-evidence-snapshot.md).

Do not invent or estimate this section.

Record only observable evidence when it exists:

- GitHub stars:
- GitHub forks:
- external contributors:
- external issues/bug reports:
- downstream references:
- package/download usage:
- documented real-world use cases:

Issue [#34](https://github.com/hesam1111111111/tradeguard-oss/issues/34) remains the dedicated community-validation track.

## Reviewer evidence path

1. README and zero-clone quickstart
2. [End-to-end integrity demo](end-to-end-integrity-demo.md)
3. [Maintainer evidence dossier](maintainer-evidence.md)
4. GitHub Actions history
5. Releases and CHANGELOG
6. Report/evidence compatibility contracts
7. SECURITY.md and CONTRIBUTING.md
8. Issue #34 for genuine external validation

## Submission gate

Before submitting:

- GitHub profile is public
- repository is public
- latest intended release is published and marked latest
- main CI is green
- README reflects current released version
- PyPI package page is reachable
- any usage/adoption claim is backed by observable evidence
- application answers stay within current field limits
- no unsupported acceptance or ecosystem-importance claim is made
