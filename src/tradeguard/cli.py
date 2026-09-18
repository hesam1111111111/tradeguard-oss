from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from math import isfinite
from pathlib import Path

from .analytics import analyze_by_closed_period, analyze_by_side, analyze_by_symbol, analyze_trades
from .diagnostics import diagnose_journal
from .importers import import_mapped_csv
from .io import load_trades_csv
from .risk import RiskBudget, RiskLimits, aggregate_exposure, analyze_initial_risk, check_risk_limits, evaluate_risk_budget
from .reconciliation import reconcile_journals

REPORT_SCHEMA = "tradeguard.report.v1"
RECONCILIATION_SCHEMA = "tradeguard.reconciliation.v1"


def _risk_payload(trades, limits: RiskLimits | None, budget: RiskBudget | None) -> dict:
    initial = analyze_initial_risk(trades)
    exposures = aggregate_exposure(trades)
    breaches = check_risk_limits(trades, limits) if limits is not None else ()
    budget_result = evaluate_risk_budget(trades, budget) if budget is not None else None
    return {
        "exposure_basis": "historical_entry_notional",
        "exposures": [asdict(item) | {"gross_notional": item.gross_notional, "net_notional": item.net_notional} for item in exposures],
        "initial_risk": {"basis": "stop_based_risk_at_entry", "total_initial_risk": initial.total_initial_risk, "measured_trades": initial.measured_trades, "diagnostics": [asdict(item) for item in initial.diagnostics]},
        "limits": asdict(limits) if limits is not None else None,
        "breaches": [asdict(item) for item in breaches],
        "budget": None if budget_result is None else {"configuration": asdict(budget), "total_initial_risk": budget_result.total_initial_risk, "measured_trades": budget_result.measured_trades, "complete": not budget_result.diagnostics, "diagnostics": [asdict(item) for item in budget_result.diagnostics], "breaches": [asdict(item) for item in budget_result.breaches]},
    }


def _segments_payload(trades, temporal_period: str | None = None) -> dict:
    payload = {
        "by_symbol": {segment.key: asdict(segment.metrics) for segment in analyze_by_symbol(trades)},
        "by_side": {segment.key: asdict(segment.metrics) for segment in analyze_by_side(trades)},
    }
    if temporal_period is not None:
        temporal = analyze_by_closed_period(trades, temporal_period)
        payload["by_closed_period"] = {
            "basis": temporal.basis,
            "period": temporal.period,
            "complete": temporal.complete,
            "measured_trades": temporal.measured_trades,
            "segments": {segment.key: asdict(segment.metrics) for segment in temporal.segments},
            "diagnostics": [asdict(item) for item in temporal.diagnostics],
        }
    return payload


def _import_payload(result) -> dict:
    return {
        "mode": "explicit_mapped_csv",
        "complete": result.complete,
        "source_rows": result.source_rows,
        "imported_rows": result.imported_rows,
        "rejected_rows": result.rejected_rows,
        "mapping": {canonical: source for canonical, source in result.mapping},
        "diagnostics": [asdict(item) for item in result.diagnostics],
    }


def build_payload(csv_path: str, limits: RiskLimits | None = None, budget: RiskBudget | None = None, temporal_period: str | None = None, import_mapping: dict[str, str] | None = None) -> dict:
    import_result = import_mapped_csv(csv_path, import_mapping) if import_mapping is not None else None
    trades = list(import_result.trades) if import_result is not None else load_trades_csv(csv_path)
    diagnostics = diagnose_journal(trades)
    import_complete = import_result is None or import_result.complete
    valid = diagnostics.valid_for_metrics and import_complete
    metrics = analyze_trades(trades) if valid else None
    diagnostics_payload = diagnostics.to_dict()
    return {
        "report_schema": REPORT_SCHEMA,
        "source": str(csv_path),
        "import": _import_payload(import_result) if import_result is not None else None,
        "journal_fingerprint": diagnostics.fingerprint,
        "metrics": asdict(metrics) if metrics is not None else None,
        "issues": diagnostics_payload["validation_issues"],
        "diagnostics": diagnostics_payload,
        "risk": _risk_payload(trades, limits, budget) if valid else None,
        "segments": _segments_payload(trades, temporal_period) if valid else None,
    }


def _reconciliation_payload(reference_path: str, candidate_path: str) -> dict:
    reference = load_trades_csv(reference_path)
    candidate = load_trades_csv(candidate_path)
    result = reconcile_journals(reference, candidate)
    return {
        "reconciliation_schema": RECONCILIATION_SCHEMA,
        "reference": str(reference_path),
        "candidate": str(candidate_path),
        "clean": result.clean,
        "reference_fingerprint": result.reference_fingerprint,
        "candidate_fingerprint": result.candidate_fingerprint,
        "reference_rows": result.reference_rows,
        "candidate_rows": result.candidate_rows,
        "exact_matches": result.exact_matches,
        "modified_rows": result.modified_rows,
        "missing": [{"record": dict(item.record), "count": item.count} for item in result.missing],
        "unexpected": [{"record": dict(item.record), "count": item.count} for item in result.unexpected],
        "mismatches": [
            {
                "identity": dict(item.identity),
                "field": item.field,
                "reference_value": item.reference_value,
                "candidate_value": item.candidate_value,
            }
            for item in result.mismatches
        ],
    }


def _positive_finite(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive finite number") from exc
    if not isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


def _mapping_entry(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("must use canonical=source_column")
    canonical, source = value.split("=", 1)
    canonical = canonical.strip()
    source = source.strip()
    if not canonical or not source:
        raise argparse.ArgumentTypeError("must use non-blank canonical=source_column")
    return canonical, source


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and analyze a trading journal CSV.")
    parser.add_argument("csv_path", help="Path to the trading journal CSV file")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--output", help="Write the deterministic JSON report to a file")
    parser.add_argument("--reconcile-with", metavar="CSV", help="Compare this canonical journal with another canonical TradeGuard CSV")
    parser.add_argument("--fail-on-drift", action="store_true", help="Exit with status 1 when reconciliation detects journal drift")
    parser.add_argument("--map", dest="mappings", action="append", type=_mapping_entry, metavar="CANONICAL=SOURCE", help="Explicit source-column mapping for generic CSV import; repeat for each mapped field")
    parser.add_argument("--group-closed-by", choices=("day", "month"), help="Add deterministic temporal metrics grouped by recorded closed_at")
    parser.add_argument("--max-gross-notional", type=_positive_finite)
    parser.add_argument("--max-symbol-gross-notional", type=_positive_finite)
    parser.add_argument("--max-trade-notional", type=_positive_finite)
    parser.add_argument("--max-trade-initial-risk", type=_positive_finite)
    parser.add_argument("--max-total-initial-risk", type=_positive_finite)
    args = parser.parse_args()

    if args.reconcile_with:
        if args.mappings:
            parser.error("--map cannot be combined with --reconcile-with")
        try:
            payload = _reconciliation_payload(args.csv_path, args.reconcile_with)
        except ValueError as exc:
            parser.error(str(exc))
        if args.output:
            Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print("TradeGuard OSS reconciliation")
            print(f"Clean: {payload['clean']}")
            print(f"Reference rows: {payload['reference_rows']}")
            print(f"Candidate rows: {payload['candidate_rows']}")
            print(f"Exact matches: {payload['exact_matches']}")
            print(f"Modified rows: {payload['modified_rows']}")
            print(f"Missing rows: {sum(item['count'] for item in payload['missing'])}")
            print(f"Unexpected rows: {sum(item['count'] for item in payload['unexpected'])}")
            print(f"Field mismatches: {len(payload['mismatches'])}")
        if args.fail_on_drift and not payload["clean"]:
            raise SystemExit(1)
        return

    import_mapping = None
    if args.mappings:
        import_mapping = {}
        for canonical, source in args.mappings:
            if canonical in import_mapping:
                parser.error(f"duplicate canonical mapping: {canonical}")
            import_mapping[canonical] = source

    limit_values = (args.max_gross_notional, args.max_symbol_gross_notional, args.max_trade_notional)
    limits = RiskLimits(args.max_gross_notional, args.max_symbol_gross_notional, args.max_trade_notional) if any(v is not None for v in limit_values) else None
    budget_values = (args.max_trade_initial_risk, args.max_total_initial_risk)
    budget = RiskBudget(args.max_trade_initial_risk, args.max_total_initial_risk) if any(v is not None for v in budget_values) else None
    try:
        payload = build_payload(args.csv_path, limits=limits, budget=budget, temporal_period=args.group_closed_by, import_mapping=import_mapping)
    except ValueError as exc:
        parser.error(str(exc))

    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return

    metrics = payload["metrics"]
    issues = payload["issues"]
    diagnostics = payload["diagnostics"]
    print("TradeGuard OSS report")
    print(f"Journal fingerprint: {payload['journal_fingerprint']}")
    if payload["import"] is not None:
        imported = payload["import"]
        print(f"Import rows: {imported['imported_rows']}/{imported['source_rows']} imported, {imported['rejected_rows']} rejected")
    if metrics is None:
        print("Metrics: skipped because journal integrity, validation, or import-integrity errors were found.")
    else:
        print(f"Trades: {metrics['trades']}")
        print(f"Win rate: {metrics['win_rate']:.2%}")
        print(f"Net PnL: {metrics['net_pnl']:.2f}")
        print(f"Expectancy: {metrics['expectancy']:.2f}")
        profit_factor = metrics["profit_factor"]
        print(f"Profit factor: {'n/a' if profit_factor is None else f'{profit_factor:.2f}'}")
        print(f"Max drawdown: {metrics['max_drawdown']:.2f}")
        risk = payload["risk"]
        print(f"Initial risk measured: {risk['initial_risk']['measured_trades']}/{metrics['trades']}")
        print(f"Total initial risk: {risk['initial_risk']['total_initial_risk']:.2f}")
        print(f"Risk-limit breaches: {len(risk['breaches'])}")
        if risk["budget"] is not None:
            print(f"Risk-budget breaches: {len(risk['budget']['breaches'])}")
        temporal = payload["segments"].get("by_closed_period")
        if temporal is not None:
            print(f"Temporal grouping: closed_at/{temporal['period']} ({temporal['measured_trades']}/{metrics['trades']} measured, complete={temporal['complete']})")
    print(f"Validation issues: {len(issues)}")
    print(f"Exact duplicates: {diagnostics['duplicate_count']}")
    for issue in issues:
        print(f"- [{issue['severity']}] row {issue['index']}: {issue['code']} - {issue['message']}")


if __name__ == "__main__":
    main()
