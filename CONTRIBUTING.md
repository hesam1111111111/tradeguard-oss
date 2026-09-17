# Contributing to TradeGuard OSS

Thanks for considering a contribution.

## Ground rules

- Keep changes narrowly scoped and explain the user-visible behavior.
- Add or update tests for behavioral changes.
- Do not commit credentials, private broker exports, personal financial data, or proprietary strategy logic.
- Prefer deterministic calculations and explicit assumptions over opaque heuristics.
- Open an issue before large architectural changes.

## Development

```bash
python -m venv .venv
pip install -e .[dev]
pytest -q
```

## Pull requests

A good pull request should include:

1. The problem being solved.
2. The implementation approach.
3. Tests added or updated.
4. Any compatibility or data-format impact.
5. Documentation changes when relevant.

## Reporting bugs

Please include a minimal reproducible example and remove any private account or trading data before posting.
