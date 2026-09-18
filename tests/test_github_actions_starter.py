from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "examples" / "github-actions" / "tradeguard.yml"
DOC = ROOT / "docs" / "github-actions-starter.md"


def test_github_actions_starter_is_present_and_fail_closed():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pip install tradeguard-oss" in workflow
    assert "--reconcile-with" in workflow
    assert "--fail-on-drift" in workflow
    assert "actions/setup-python@v5" in workflow


def test_github_actions_starter_docs_cover_scope_and_paths():
    doc = DOC.read_text(encoding="utf-8")
    assert ".github/workflows/tradeguard.yml" in doc
    assert "trusted baseline journal" in doc
    assert "Do not commit credentials" in doc
    assert "does not connect to brokers" in doc
