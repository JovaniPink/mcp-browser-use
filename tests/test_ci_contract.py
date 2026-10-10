"""Workflow contracts for supported Python versions and the security gate."""

from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml"


def test_functional_matrix_covers_documented_python_versions() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'python: ["3.11", "3.12", "3.13", "3.14"]' in workflow


def test_runtime_audit_is_a_separate_unsuppressed_job() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "name: Runtime dependency audit" in workflow
    assert "pip-audit -r /tmp/requirements.txt" in workflow
    assert "--ignore-vuln" not in workflow
