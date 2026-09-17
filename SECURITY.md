# Security Policy

## Scope

TradeGuard OSS performs local journal parsing, validation, deterministic analytics, historical risk analysis, mapped CSV importing, and report generation. The core package does not require broker or exchange credentials and does not place orders.

## Sensitive data

Do not include API keys, access tokens, passwords, account identifiers, private broker exports, or personal financial records in issues, pull requests, examples, or test fixtures.

## Reporting a vulnerability

If a security issue could expose credentials, private financial data, corrupt report integrity, or enable unsafe behavior, do not publish exploit details in a public issue. Contact the repository maintainer privately through an appropriate GitHub-supported channel until a dedicated security advisory workflow is configured.

## Execution boundary

TradeGuard OSS is a historical/local-file analytics toolkit. It is not a broker connector, live account synchronization service, trading signal engine, or order-execution system. Security claims and tests should be evaluated within that boundary.
