from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .analytics import analyze_trades
from .io import load_trades_csv
from .validation import validate_trades


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and analyze a trading journal CSV.")
    parser.add_argument("csv_path", help="Path to the trading journal CSV file")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    trades = load_trades_csv(args.csv_path)
    metrics = analyze_trades(trades)
    issues = validate_trades(trades)

    payload = {
        "metrics": asdict(metrics),
        "issues": [asdict(issue) for issue in issues],
    }

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
        return

    print("TradeGuard OSS report")
    print(f"Trades: {metrics.trades}")
    print(f"Win rate: {metrics.win_rate:.2%}")
    print(f"Net PnL: {metrics.net_pnl:.2f}")
    print(f"Expectancy: {metrics.expectancy:.2f}")
    print(f"Max drawdown: {metrics.max_drawdown:.2f}")
    print(f"Validation issues: {len(issues)}")
    for issue in issues:
        print(f"- [{issue.severity}] row {issue.index}: {issue.code} - {issue.message}")


if __name__ == "__main__":
    main()
