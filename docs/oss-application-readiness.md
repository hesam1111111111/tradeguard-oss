# OSS application readiness

This document tracks public-repository readiness for maintainer-support programs and similar OSS reviews. It is intentionally factual and should not claim eligibility or acceptance.

## Repository evidence

- Public repository with MIT license.
- Active issue and pull-request history.
- Versioned releases and changelog.
- Automated CI across Python 3.10–3.13.
- Distribution build and wheel smoke-install validation.
- Security, contribution, and report-contract documentation.
- Synthetic/privacy-safe examples only.
- Historical/local-file analytics scope; no broker credentials or order execution.

## Maintainer-workflow evidence

A concise externally reviewable trail is maintained in [`docs/maintainer-evidence.md`](maintainer-evidence.md).

The repository uses scoped issues, reviewable branches, pull requests, CI gates, release preparation, changelog updates, and explicit compatibility contracts. These are intended to make maintenance activity visible and reproducible.

## Remaining external signals

Repository quality alone does not establish ecosystem importance or adoption. Useful external evidence includes genuine users, stars/forks, downstream references, bug reports, outside contributions, package/download usage, and documented use cases. These signals should grow organically; they should never be fabricated.

## Application checklist

- GitHub profile public.
- Repository public.
- Latest release published and marked latest.
- README accurately reflects current release and scope.
- SECURITY.md and CONTRIBUTING.md current.
- CI green on the release commit/PR.
- Application description explains the concrete maintenance burden: triage, review, releases, compatibility, security, and data-quality guarantees.
- Any usage/adoption claims are backed by observable evidence.
