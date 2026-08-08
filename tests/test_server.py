"""Security-boundary tests for the MCP server entrypoint."""

from __future__ import annotations

import asyncio

import pytest

from mcp_browser_use import server


def test_tool_input_is_trimmed():
    assert server._validated_tool_input("  Open example.com  ", "  context  ") == (
        "Open example.com",
        "context",
    )


def test_empty_task_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        server._validated_tool_input("  ", "")


@pytest.mark.parametrize(
    ("task", "add_infos", "field"),
    (
        ("x" * (server._MAX_TASK_CHARS + 1), "", "task"),
        ("Open example.com", "x" * (server._MAX_CONTEXT_CHARS + 1), "add_infos"),
    ),
)
def test_tool_input_limits_are_enforced(task, add_infos, field):
    with pytest.raises(ValueError, match=rf"{field} must not exceed"):
        server._validated_tool_input(task, add_infos)


@pytest.mark.parametrize(
    ("name", "value", "default", "minimum", "maximum"),
    (
        ("MCP_MAX_STEPS", "0", 30, 1, 100),
        ("MCP_MAX_STEPS", "101", 30, 1, 100),
        ("MCP_MAX_ACTIONS_PER_STEP", "0", 5, 1, 20),
        ("MCP_MAX_ACTIONS_PER_STEP", "21", 5, 1, 20),
        ("MCP_MAX_STEPS", "not-an-integer", 30, 1, 100),
    ),
)
def test_runtime_limits_reject_invalid_or_unsafe_values(
    monkeypatch, name, value, default, minimum, maximum
):
    monkeypatch.setenv(name, value)
    assert (
        server._env_int(name, default, minimum=minimum, maximum=maximum) == default
    )


def test_invalid_task_is_rejected_before_resource_allocation(monkeypatch):
    def fail_if_called(*args, **kwargs):
        pytest.fail("invalid task allocated a model or browser session")

    monkeypatch.setattr(server.utils, "get_llm_model", fail_if_called)
    monkeypatch.setattr(server, "create_browser_session", fail_if_called)

    with pytest.raises(ValueError, match="must not be empty"):
        asyncio.run(server.run_browser_agent("  "))
