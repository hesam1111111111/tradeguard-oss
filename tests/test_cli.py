import json
from pathlib import Path

from tradeguard.cli import build_payload, main


def test_build_payload_has_versioned_report_schema(tmp_path: Path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,1\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal))
    assert payload["report_schema"] == "tradeguard.report.v1"
    assert payload["metrics"]["trades"] == 1
    assert payload["metrics"]["net_pnl"] == 10.0


def test_cli_writes_deterministic_json_report(tmp_path: Path, monkeypatch):
    journal = tmp_path / "journal.csv"
    report = tmp_path / "report.json"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity\nBTCUSDT,long,100,110,95,1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["tradeguard", str(journal), "--output", str(report), "--json"])
    main()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["report_schema"] == "tradeguard.report.v1"
    assert data["metrics"]["profit_factor"] is not None
