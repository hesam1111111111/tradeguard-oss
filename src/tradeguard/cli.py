from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .analytics import analyze_trades
from .diagnostics import diagnose_journal
from .io import load_trades_csv
from .risk import RiskLimits, aggregate_exposure, analyze_initial_risk, check_risk_limits

REPORT_SCHEMA = "tradeguard.report.v1"


def _risk_payload(trades, limits: RiskLimits | None) -> dict:
    initial = analyze_initial_risk(trades)
    exposures = aggregate_exposure(trades)
    breaches = check_risk_limits(trades, limits) if limits is not None else ()
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
    }


def build_payload(csv_path: str, limits: RiskLimits | None = None) -> dict:
    trades = load_trades_csv(csv_path)
    diagnostics = diagnose_journal(trades)
    metrics = analyze_trades(trades) if diagnostics.valid_for_metrics else None
    diagnostics_payload = diagnostics.to_dict()
    risk = _risk_payload(trades, limits) if diagnostics.valid_for_metrics else None
    return {
        "report_schema": REPORT_SCHEMA,
        "source": str(csv_path),
        "journal_fingerprint": diagnostics.fingerprint,
        "metrics": asdict(metrics) if metrics is not None else None,
        "issues": diagnostics_payload["validation_issues"],
        "diagnostics": diagnostics_payload,
        "risk": risk,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and analyze a trading journal CSV.")
    parser.add_argument("csv_path", help="Path to the trading journal CSV file")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--output", help="Write the deterministic JSON report to a file")
    parser.add_argument("--max-gross-notional", type=float)
    parser.add_argument("--max-symbol-gross-notional", type=float)
    parser.add_argument("--max-trade-notional", type=float)
    args = parser.parse_args()

    limit_values = (args.max_gross_notional, args.max_symbol_gross_notional, args.max_trade_notional)
    limits = None
    if any(value is not None for value in limit_values):
        limits = RiskLimits(
            max_gross_notional=args.max_gross_notional,
            max_symbol_gross_notional=args.max_symbol_gross_notional,
            max_trade_notional=args.max_trade_notional,
        )

    payload = build_payload(args.csv_path, limits=limits)

    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )

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
    print(f"Validation issues: {len(issues)}")
    print(f"Exact duplicates: {diagnostics['duplicate_count']}")
    for issue in issues:
        print(f"- [{issue['severity']}] row {issue['index']}: {issue['code']} - {issue['message']}")


if __name__ == "__main__":
    main()
