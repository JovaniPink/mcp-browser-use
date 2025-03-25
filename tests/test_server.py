import pytest
import asyncio
from unittest.mock import patch, MagicMock

from mcp_browser_use.server import run_browser_agent, main


# Demonstration test for run_browser_agent
@pytest.mark.asyncio
async def test_run_browser_agent_succeeds(monkeypatch):
    # Mock environment variables
    monkeypatch.setenv("MCP_MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("MCP_MODEL_NAME", "claude-3-5-sonnet-20241022")

    # Mock get_llm_model to return a fake LLM
    with patch("mcp_browser_use.utils.utils.get_llm_model") as mock_llm:
        mock_llm.return_value = MagicMock()

        # Mock the CustomBrowser so it won’t try to launch a real browser
        with patch(
            "mcp_browser_use.browser.custom_browser.CustomBrowser"
        ) as mock_browser:
            mock_browser.return_value.new_context = MagicMock()
            mock_browser.return_value.close = MagicMock()

            # Mock the CustomAgent so it won’t actually do anything
            with patch("mcp_browser_use.agent.custom_agent.CustomAgent") as mock_agent:
                mock_instance = MagicMock()
                mock_instance.run = MagicMock(
                    side_effect=lambda max_steps: asyncio.Future()
                )
                fake_history = MagicMock()
                fake_history.final_result.return_value = "Mocked final result"

                # The future must return a valid object
                f = asyncio.Future()
                f.set_result(fake_history)

                mock_instance.run.return_value = f
                mock_agent.return_value = mock_instance

                # Run the tool
                result = await run_browser_agent("sample task", "some extra info")

                # Verify result
                assert result == "Mocked final result"


# A simple synchronous test for main()
# We can’t truly spin up the server in a test environment, but we can verify it doesn’t crash.
@pytest.mark.parametrize("exception", [None, Exception("Test error")])
def test_main(exception):
    with patch("mcp_browser_use.server.app.run") as mock_run:
        if exception:
            mock_run.side_effect = exception
        # We just call main and ensure it doesn’t blow up
        try:
            main()
        except Exception as e:
            assert str(e) == "Test error"
