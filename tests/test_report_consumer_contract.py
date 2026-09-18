import json
from pathlib import Path

from tradeguard.cli import build_payload

_REQUIRED_TOP_LEVEL = {
    "report_schema": str,
    "source": str,
    "import": (dict, type(None)),
    "journal_fingerprint": str,
    "metrics": (dict, type(None)),
    "issues": list,
    "diagnostics": dict,
    "risk": (dict, type(None)),
    "segments": (dict, type(None)),
}


def _representative_report(tmp_path: Path) -> dict:
    journal = tmp_path / "consumer-fixture.csv"
    journal.write_text(
        "symbol,side,entry,exit,stop_loss,quantity,closed_at\n"
        "BTCUSDT,long,100,110,95,2,2026-09-01T10:00:00\n"
        "ETHUSDT,short,50,45,55,1,2026-09-02T11:00:00\n",
        encoding="utf-8",
    )
    payload = build_payload(str(journal), temporal_period="day")
    payload["source"] = "consumer-fixture.csv"
    return payload


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n").encode()


def test_report_v1_established_top_level_contract(tmp_path: Path):
    payload = _representative_report(tmp_path)
    assert payload["report_schema"] == "tradeguard.report.v1"
    for name, expected_type in _REQUIRED_TOP_LEVEL.items():
        assert name in payload
        assert isinstance(payload[name], expected_type)
    assert len(payload["journal_fingerprint"]) == 64
    assert payload["metrics"]["trades"] == 2
    assert payload["segments"]["by_closed_period"]["complete"] is True


def test_report_v1_serialization_is_byte_stable(tmp_path: Path):
    first = _representative_report(tmp_path)
    second = _representative_report(tmp_path)
    assert _canonical_bytes(first) == _canonical_bytes(second)


def test_report_v1_consumer_can_ignore_additive_unknown_fields(tmp_path: Path):
    payload = _representative_report(tmp_path)
    established = {name: payload[name] for name in _REQUIRED_TOP_LEVEL}
    payload["future_optional_member"] = {"ignored_by_v1_consumer": True}
    consumed = {name: payload[name] for name in _REQUIRED_TOP_LEVEL}
    assert consumed == established
