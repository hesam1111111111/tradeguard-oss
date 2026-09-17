from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .analytics import analyze_trades
from .io import load_trades_csv
from .validation import validate_trades


def build_payload(csv_path: str) -> dict:
    trades = load_trades_csv(csv_path)
    issues = validate_trades(trades)
    has_errors = any(issue.severity == "error" for issue in issues)
    metrics = None if has_errors else analyze_trades(trades)
    return {
        "report_schema": "tradeguard.report.v1",
        "source": str(csv_path),
        "metrics": asdict(metrics) if metrics is not None else None,
        "issues": [asdict(issue) for issue in issues],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and analyze a trading journal CSV.")
    parser.add_argument("csv_path", help="Path to the trading journal CSV file")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--output", help="Write the deterministic JSON report to a file")
    args = parser.parse_args()

    payload = build_payload(args.csv_path)

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
    print("TradeGuard OSS report")
    if metrics is None:
        print("Metrics: skipped because validation errors were found.")
    else:
        print(f"Trades: {metrics['trades']}")
        print(f"Win rate: {metrics['win_rate']:.2%}")
        print(f"Net PnL: {metrics['net_pnl']:.2f}")
        print(f"Expectancy: {metrics['expectancy']:.2f}")
        print(f"Profit factor: {metrics['profit_factor']:.2f}")
        print(f"Max drawdown: {metrics['max_drawdown']:.2f}")
    print(f"Validation issues: {len(issues)}")
    for issue in issues:
        print(f"- [{issue['severity']}] row {issue['index']}: {issue['code']} - {issue['message']}")


if __name__ == "__main__":
    main()
