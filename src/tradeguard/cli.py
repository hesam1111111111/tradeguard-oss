from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from math import isfinite
from pathlib import Path

from .analytics import analyze_by_side, analyze_by_symbol, analyze_trades
from .diagnostics import diagnose_journal
from .io import load_trades_csv
from .risk import RiskBudget, RiskLimits, aggregate_exposure, analyze_initial_risk, check_risk_limits, evaluate_risk_budget

REPORT_SCHEMA = "tradeguard.report.v1"


def _risk_payload(trades, limits: RiskLimits | None, budget: RiskBudget | None) -> dict:
    initial = analyze_initial_risk(trades)
    exposures = aggregate_exposure(trades)
    breaches = check_risk_limits(trades, limits) if limits is not None else ()
    budget_result = evaluate_risk_budget(trades, budget) if budget is not None else None
    return {
        "exposure_basis": "historical_entry_notional",
        "exposures": [asdict(item) | {"gross_notional": item.gross_notional, "net_notional": item.net_notional} for item in exposures],
        "initial_risk": {
            "basis": "stop_based_risk_at_entry",
            "total_initial_risk": initial.total_initial_risk,
            "measured_trades": initial.measured_trades,
            "diagnostics": [asdict(item) for item in initial.diagnostics],
        },
        "limits": asdict(limits) if limits is not None else None,
        "breaches": [asdict(item) for item in breaches],
        "budget": None if budget_result is None else {
            "configuration": asdict(budget),
            "total_initial_risk": budget_result.total_initial_risk,
            "measured_trades": budget_result.measured_trades,
            "complete": not budget_result.diagnostics,
            "diagnostics": [asdict(item) for item in budget_result.diagnostics],
            "breaches": [asdict(item) for item in budget_result.breaches],
        },
    }


def _segments_payload(trades) -> dict:
    return {
        "by_symbol": {segment.key: asdict(segment.metrics) for segment in analyze_by_symbol(trades)},
        "by_side": {segment.key: asdict(segment.metrics) for segment in analyze_by_side(trades)},
    }


def build_payload(csv_path: str, limits: RiskLimits | None = None, budget: RiskBudget | None = None) -> dict:
    trades = load_trades_csv(csv_path)
    diagnostics = diagnose_journal(trades)
    valid = diagnostics.valid_for_metrics
    metrics = analyze_trades(trades) if valid else None
    diagnostics_payload = diagnostics.to_dict()
    return {
        "report_schema": REPORT_SCHEMA,
        "source": str(csv_path),
        "journal_fingerprint": diagnostics.fingerprint,
        "metrics": asdict(metrics) if metrics is not None else None,
        "issues": diagnostics_payload["validation_issues"],
        "diagnostics": diagnostics_payload,
        "risk": _risk_payload(trades, limits, budget) if valid else None,
        "segments": _segments_payload(trades) if valid else None,
    }


def _positive_finite(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive finite number") from exc
    if not isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and analyze a trading journal CSV.")
    parser.add_argument("csv_path", help="Path to the trading journal CSV file")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--output", help="Write the deterministic JSON report to a file")
    parser.add_argument("--max-gross-notional", type=_positive_finite)
    parser.add_argument("--max-symbol-gross-notional", type=_positive_finite)
    parser.add_argument("--max-trade-notional", type=_positive_finite)
    parser.add_argument("--max-trade-initial-risk", type=_positive_finite)
    parser.add_argument("--max-total-initial-risk", type=_positive_finite)
    args = parser.parse_args()

    limit_values = (args.max_gross_notional, args.max_symbol_gross_notional, args.max_trade_notional)
    limits = RiskLimits(args.max_gross_notional, args.max_symbol_gross_notional, args.max_trade_notional) if any(v is not None for v in limit_values) else None
    budget_values = (args.max_trade_initial_risk, args.max_total_initial_risk)
    budget = RiskBudget(args.max_trade_initial_risk, args.max_total_initial_risk) if any(v is not None for v in budget_values) else None
    payload = build_payload(args.csv_path, limits=limits, budget=budget)

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
    if metrics is None:
        print("Metrics: skipped because journal integrity or validation errors were found.")
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
    print(f"Validation issues: {len(issues)}")
    print(f"Exact duplicates: {diagnostics['duplicate_count']}")
    for issue in issues:
        print(f"- [{issue['severity']}] row {issue['index']}: {issue['code']} - {issue['message']}")


if __name__ == "__main__":
    main()
