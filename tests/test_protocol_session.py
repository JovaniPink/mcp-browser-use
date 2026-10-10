"""Exercise the installed MCP transport without allocating a model or browser."""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_browser_use import server


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_protocol_lists_and_calls_the_registered_tool(monkeypatch, mode):
    calls = []

    async def execute(task, add_infos):
        calls.append((task, add_infos))
        return "synthetic protocol result"

    monkeypatch.setattr(server, "execute_browser_agent", execute)
    async with Client(server.app, mode=mode) as client:
        tools = await client.list_tools()
        assert [tool.name for tool in tools] == ["run_browser_agent"]
        assert tools[0].input_schema["required"] == ["task"]
        result = await client.call_tool("run_browser_agent", {"task": "synthetic"})
        assert result.data == "synthetic protocol result"
    assert calls == [("synthetic", "")]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_protocol_rejects_empty_input_before_provider_allocation(
    monkeypatch, mode
):
    allocations = []

    def allocate(*args, **kwargs):
        allocations.append(True)
        raise AssertionError("Provider allocation must not occur")

    monkeypatch.setattr(server, "get_llm_model", allocate)
    async with Client(server.app, mode=mode) as client:
        with pytest.raises(ToolError, match="task must not be empty"):
            await client.call_tool("run_browser_agent", {"task": " "})
    assert allocations == []
