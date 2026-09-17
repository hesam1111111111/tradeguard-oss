# Security Policy

## Scope

TradeGuard OSS currently performs local journal parsing, validation, and analytics. The core package does not require broker or exchange credentials.

## Sensitive data

Do not include API keys, access tokens, passwords, account identifiers, private broker exports, or personal financial records in issues, pull requests, examples, or test fixtures.

## Reporting a vulnerability

If a security issue could expose credentials, private financial data, or enable unsafe execution behavior, do not publish exploit details in a public issue. Contact the repository maintainer privately through an appropriate GitHub-supported channel until a dedicated security advisory workflow is configured.

## Execution boundary

TradeGuard OSS v0.1.x does not place orders and should not be treated as an execution or portfolio-risk control system.
