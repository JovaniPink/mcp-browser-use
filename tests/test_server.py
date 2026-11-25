import asyncio
import dataclasses

import pytest

from mcp_browser_use import server


class DummyHistory:
    def final_result(self):
        return "completed"


class DummyBrowserSession:
    def __init__(self, *, fail_stop=False):
        self.fail_stop = fail_stop
        self.stopped = False
        self.killed = False

    async def stop(self):
        self.stopped = True
        if self.fail_stop:
            raise RuntimeError("stop failed")

    async def kill(self):
        self.killed = True


class DummyAgent:
    created_kwargs = None
    max_steps = None

    def __init__(self, **kwargs):
        type(self).created_kwargs = kwargs

    async def run(self, *, max_steps):
        type(self).max_steps = max_steps
        return DummyHistory()


@pytest.mark.asyncio
async def test_execute_browser_agent_uses_public_agent_and_cleans_up(monkeypatch):
    browser = DummyBrowserSession()
    monkeypatch.setattr(server, "Agent", DummyAgent)
    monkeypatch.setattr(server, "create_browser_session", lambda: browser)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())
    monkeypatch.setenv("MCP_MAX_STEPS", "12")

    result = await server.execute_browser_agent("Open example.com", "Read the title")

    assert result == "completed"
    assert DummyAgent.max_steps == 12
    assert DummyAgent.created_kwargs["task"] == (
        "Open example.com\n\nAdditional context:\nRead the title"
    )
    assert browser.stopped is True


@pytest.mark.asyncio
async def test_execute_browser_agent_forces_cleanup_after_stop_failure(monkeypatch):
    browser = DummyBrowserSession(fail_stop=True)
    monkeypatch.setattr(server, "Agent", DummyAgent)
    monkeypatch.setattr(server, "create_browser_session", lambda: browser)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())

    await server.execute_browser_agent("Open example.com")

    assert browser.killed is True


def test_runtime_config_bounds_untrusted_limits(monkeypatch):
    monkeypatch.setenv("MCP_MAX_STEPS", "9999")
    monkeypatch.setenv("MCP_MAX_ACTIONS_PER_STEP", "0")

    runtime = server.AgentRuntimeConfig.from_env()

    assert runtime.max_steps == 100
    assert runtime.max_actions_per_step == 1


def test_empty_task_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        server._task_with_context("  ", "")


@pytest.mark.parametrize(
    ("task", "add_infos", "field"),
    (
        ("x" * (server._MAX_TASK_CHARS + 1), "", "task"),
        ("Open example.com", "x" * (server._MAX_CONTEXT_CHARS + 1), "add_infos"),
    ),
)
def test_task_input_limits_are_enforced(task, add_infos, field):
    with pytest.raises(ValueError, match=rf"{field} must not exceed"):
        server._task_with_context(task, add_infos)


@pytest.mark.asyncio
async def test_invalid_task_is_rejected_before_resource_allocation(monkeypatch):
    def fail_if_called(*args, **kwargs):
        pytest.fail("invalid task allocated a model or browser session")

    monkeypatch.setattr(server, "get_llm_model", fail_if_called)
    monkeypatch.setattr(server, "create_browser_session", fail_if_called)

    with pytest.raises(ValueError, match="must not be empty"):
        await server.execute_browser_agent("  ")


def test_runtime_config_defaults_leave_temperature_to_the_provider(monkeypatch):
    for name in ("MCP_TEMPERATURE", "MCP_RUN_TIMEOUT_SECONDS", "MCP_MODEL_NAME"):
        monkeypatch.delenv(name, raising=False)

    runtime = server.AgentRuntimeConfig.from_env()

    assert runtime.temperature is None
    assert runtime.timeout_seconds == 600
    assert runtime.model == "claude-opus-5"


@pytest.mark.parametrize(
    ("raw", "expected"),
    (("0.7", 0.7), ("9", 2.0), ("-1", 0.0), ("warm", None), ("  ", None)),
)
def test_runtime_config_bounds_temperature(monkeypatch, raw, expected):
    monkeypatch.setenv("MCP_TEMPERATURE", raw)

    assert server.AgentRuntimeConfig.from_env().temperature == expected


@pytest.mark.parametrize(("raw", "expected"), (("5", 30), ("99999", 3600), ("x", 600)))
def test_runtime_config_bounds_run_timeout(monkeypatch, raw, expected):
    monkeypatch.setenv("MCP_RUN_TIMEOUT_SECONDS", raw)

    assert server.AgentRuntimeConfig.from_env().timeout_seconds == expected


class HangingAgent(DummyAgent):
    async def run(self, *, max_steps):
        await asyncio.sleep(3600)


@pytest.mark.asyncio
async def test_timed_out_run_is_reported_and_releases_the_browser(monkeypatch):
    browser = DummyBrowserSession()
    runtime = dataclasses.replace(
        server.AgentRuntimeConfig.from_env(), timeout_seconds=0.01
    )
    monkeypatch.setattr(server.AgentRuntimeConfig, "from_env", lambda: runtime)
    monkeypatch.setattr(server, "Agent", HangingAgent)
    monkeypatch.setattr(server, "create_browser_session", lambda: browser)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())

    with pytest.raises(RuntimeError, match="timed out after"):
        await server.execute_browser_agent("Open example.com")

    assert browser.stopped is True


@pytest.mark.asyncio
async def test_concurrent_runs_are_limited_to_the_configured_slots(monkeypatch):
    active = 0
    peak = 0

    class SlowAgent(DummyAgent):
        async def run(self, *, max_steps):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)
            active -= 1
            return DummyHistory()

    monkeypatch.setattr(server, "_run_slots", asyncio.Semaphore(2))
    monkeypatch.setattr(server, "Agent", SlowAgent)
    monkeypatch.setattr(server, "create_browser_session", DummyBrowserSession)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())

    results = await asyncio.gather(
        *(server.execute_browser_agent(f"Task {index}") for index in range(5))
    )

    assert results == ["completed"] * 5
    assert peak == 2


class InnerTimeoutAgent(DummyAgent):
    async def run(self, *, max_steps):
        raise TimeoutError("provider request timed out")


@pytest.mark.asyncio
async def test_inner_timeout_is_not_reported_as_the_run_deadline(monkeypatch):
    browser = DummyBrowserSession()
    monkeypatch.setattr(server, "Agent", InnerTimeoutAgent)
    monkeypatch.setattr(server, "create_browser_session", lambda: browser)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())

    with pytest.raises(RuntimeError, match="inspect server logs"):
        await server.execute_browser_agent("Open example.com")

    assert browser.stopped is True
