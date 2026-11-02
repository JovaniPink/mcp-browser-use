"""Architecture checks that keep browser-use integration on supported APIs."""

from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "mcp_browser_use"
FORBIDDEN_IMPORTS = (
    "browser_use.agent.service",
    "browser_use.agent.message_manager",
    "browser_use.controller.service",
    "browser_use.telemetry",
)


def test_source_does_not_import_private_browser_use_layers():
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(SOURCE_ROOT.rglob("*.py"))
    )

    for import_path in FORBIDDEN_IMPORTS:
        assert import_path not in source


def test_server_uses_root_public_agent_and_session_exports():
    server_source = (SOURCE_ROOT / "server.py").read_text(encoding="utf-8")

    assert "from browser_use import Agent, BrowserSession" in server_source
