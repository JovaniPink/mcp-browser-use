"""Cancellation must complete browser cleanup before another run gets the slot."""

import asyncio

import anyio
import pytest

from mcp_browser_use import server


@pytest.mark.asyncio
async def test_cancelled_request_completes_cleanup_before_reusing_slot(monkeypatch):
    events = []
    first_started = anyio.Event()
    cleanup_entered = anyio.Event()
    allow_cleanup = anyio.Event()
    first_finished = anyio.Event()
    second_finished = anyio.Event()
    cancellation = {}
    browser_count = 0

    class Browser:
        def __init__(self, number):
            self.number = number

        async def stop(self):
            if self.number == 1:
                cleanup_entered.set()
                await allow_cleanup.wait()
            await anyio.sleep(0)
            events.append(f"cleaned:{self.number}")

        async def kill(self):
            await anyio.sleep(0)
            events.append(f"killed:{self.number}")

    class History:
        def final_result(self):
            return "finished"

    class Agent:
        def __init__(self, task, **kwargs):
            self.task = task

        async def run(self, **kwargs):
            events.append(f"started:{self.task}")
            if self.task == "first":
                first_started.set()
                await anyio.sleep_forever()
            return History()

    def create_browser():
        nonlocal browser_count
        browser_count += 1
        return Browser(browser_count)

    async def first_request():
        with anyio.CancelScope() as scope:
            cancellation["scope"] = scope
            await server.execute_browser_agent("first")
        first_finished.set()

    async def second_request():
        assert await server.execute_browser_agent("second") == "finished"
        second_finished.set()

    monkeypatch.setattr(server, "Agent", Agent)
    monkeypatch.setattr(server, "create_browser_session", create_browser)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())
    monkeypatch.setattr(server, "_run_slots", asyncio.Semaphore(1))

    with anyio.fail_after(5):
        async with anyio.create_task_group() as group:
            group.start_soon(first_request)
            await first_started.wait()
            cancellation["scope"].cancel()
            await cleanup_entered.wait()
            group.start_soon(second_request)
            try:
                await anyio.sleep(0)
            finally:
                allow_cleanup.set()
            await first_finished.wait()
            await second_finished.wait()

    assert "cleaned:1" in events
    assert events.index("cleaned:1") < events.index("started:second")
    assert events.count("cleaned:2") == 1


@pytest.mark.asyncio
async def test_cancelled_cleanup_forces_shutdown_after_graceful_deadline(monkeypatch):
    events = []

    class Browser:
        async def stop(self):
            events.append("stop")
            await anyio.sleep_forever()

        async def kill(self):
            await anyio.sleep(0)
            events.append("kill-completed")

    monkeypatch.setattr(server, "_BROWSER_STOP_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(server, "_BROWSER_KILL_TIMEOUT_SECONDS", 0.1)

    with anyio.fail_after(1):
        with anyio.CancelScope() as scope:
            scope.cancel()
            await server._close_browser_session(Browser())

    assert events == ["stop", "kill-completed"]


@pytest.mark.asyncio
async def test_forced_cleanup_also_has_a_deadline(monkeypatch, caplog):
    events = []

    class Browser:
        async def stop(self):
            events.append("stop")
            await anyio.sleep_forever()

        async def kill(self):
            events.append("kill")
            await anyio.sleep_forever()

    monkeypatch.setattr(server, "_BROWSER_STOP_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(server, "_BROWSER_KILL_TIMEOUT_SECONDS", 0.01)

    await asyncio.wait_for(server._close_browser_session(Browser()), timeout=1)

    assert events == ["stop", "kill"]
    assert "Forced browser shutdown failed or timed out" in caplog.text


@pytest.mark.asyncio
async def test_native_cancellation_during_stop_is_preserved_after_fallback(monkeypatch):
    stopping = asyncio.Event()
    killed = []

    class Browser:
        async def stop(self):
            stopping.set()
            await asyncio.sleep(3600)

        async def kill(self):
            await anyio.sleep(0)
            killed.append(True)

    class History:
        def final_result(self):
            return "finished"

    class Agent:
        def __init__(self, **kwargs):
            pass

        async def run(self, **kwargs):
            return History()

    monkeypatch.setattr(server, "Agent", Agent)
    monkeypatch.setattr(server, "create_browser_session", Browser)
    monkeypatch.setattr(server, "get_llm_model", lambda *args, **kwargs: object())
    monkeypatch.setattr(server, "_run_slots", asyncio.Semaphore(1))

    task = asyncio.create_task(server.execute_browser_agent("first"))
    await asyncio.wait_for(stopping.wait(), timeout=1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert killed == [True]
