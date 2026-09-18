# Mapped CSV import preview

TradeGuard supports deterministic, explicit CSV column mapping. It never guesses source-column aliases.

Use `--import-preview` before analysis to inspect what would import and what would be rejected:

```bash
tradeguard external.csv --import-preview --json \
  --map symbol=ticker \
  --map side=direction \
  --map entry=open_px \
  --map exit=close_px
```

Preview is read-only. It reports source, importable, and rejected row counts plus field-level diagnostics. Stable diagnostic codes include `missing_required_value`, `invalid_number`, and `invalid_datetime`; `invalid_mapped_row` remains a compatibility fallback for unexpected row-construction failures.

Missing mapped source columns fail before row processing. Rejected rows do not cause preview itself to fail, allowing the result to be used as a safe pre-import inspection step.
