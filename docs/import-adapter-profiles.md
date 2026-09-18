# Explicit import adapter profiles

TradeGuard import profiles are named, immutable column mappings for known CSV shapes. They are an offline convenience layer over `import_mapped_csv`; they do not detect brokers, guess aliases, connect to accounts, or handle credentials.

Callers must explicitly select a profile:

```python
from tradeguard import available_import_profiles, import_csv_with_profile

print(available_import_profiles())
result = import_csv_with_profile("journal.csv", "generic_ticket_export")
```

Built-in profiles use synthetic generic export shapes so the public package does not imply compatibility with a broker format that has not been independently validated. A broker- or journal-specific profile should be added only with a sanitized fixture, documented export/version assumptions, deterministic tests against canonical TradeGuard CSV, and no private financial data.

Unknown profile names fail closed. The underlying mapped-import diagnostics, provenance, source-integrity checks, and completeness rules remain authoritative.
