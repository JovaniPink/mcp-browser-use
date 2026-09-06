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
