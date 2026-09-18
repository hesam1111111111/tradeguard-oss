# GitHub Actions starter

This example shows how to use TradeGuard OSS as a repository-level CI gate without cloning TradeGuard, writing Python code, or connecting to a broker.

## What it does

The workflow:

- installs `tradeguard-oss` directly from PyPI;
- validates a journal deterministically;
- reconciles a reference journal against a candidate journal;
- exits non-zero when drift is detected.

## Copy-paste workflow

Create `.github/workflows/tradeguard.yml` in your own repository:

```yaml
name: TradeGuard journal integrity

on:
  pull_request:
  push:

jobs:
  tradeguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install TradeGuard OSS
        run: pip install tradeguard-oss

      - name: Validate journal
        run: tradeguard examples/integrity_reference.csv --json

      - name: Fail if journal drift is detected
        run: |
          tradeguard examples/integrity_reference.csv \
            --reconcile-with examples/integrity_candidate.csv \
            --fail-on-drift

```

Replace:

- `examples/integrity_reference.csv` with the path to your trusted baseline journal;
- `examples/integrity_candidate.csv` with the path to the journal/export you want to compare.

## Expected behavior

- clean validation + no reconciliation drift: CI can pass;
- validation failure: TradeGuard reports the journal problem;
- reconciliation drift with `--fail-on-drift`: the workflow fails intentionally.

This makes journal migration, export, backup, and downstream-data checks reviewable in pull requests.

## Privacy and scope

Use only privacy-safe files suitable for your own repository or CI environment. Do not commit credentials, broker API keys, account identifiers, or private financial records.

TradeGuard does not connect to brokers and does not verify real execution, trader identity, profitability, or strategy quality.
