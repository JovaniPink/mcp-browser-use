"""Offline backend for exercising the real server over subprocess MCP stdio."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anyio
import psutil
from browser_use import BrowserSession

from mcp_browser_use import server
from mcp_browser_use.browser import browser_manager

EVENTS = Path(os.environ["MCP_COMPAT_EVENTS"])
WORKSPACE = Path(os.environ["MCP_COMPAT_WORKSPACE"])
BROWSER = os.environ.get("MCP_COMPAT_BROWSER")
OWNED: dict[str, list[dict]] = {}
COUNTER = 0


def emit(kind: str, **values) -> None:
    with EVENTS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": kind, **values}) + "\n")


def surviving_processes(identity: str) -> list[int]:
    alive = []
    for item in OWNED.get(identity, []):
        try:
            process = psutil.Process(item["pid"])
            if (
                process.create_time() == item["created"]
                and process.is_running()
                and process.status() != psutil.STATUS_ZOMBIE
            ):
                alive.append(process.pid)
        except psutil.NoSuchProcess:
            pass
    return alive


async def record_cleanup(identity: str, method: str) -> None:
    # A real checkpoint is essential: a cancelled MCP scope otherwise makes a
    # synchronous test double falsely appear to clean up successfully.
    await anyio.sleep(0.05)
    with anyio.move_on_after(2):
        while surviving_processes(identity):
            await anyio.sleep(0.02)
    emit(
        "cleanup-complete",
        identity=identity,
        method=method,
        alive=surviving_processes(identity),
    )


class ObservedBrowser(BrowserSession):
    async def stop(self) -> None:
        emit("cleanup-entered", identity=self.id, method="stop")
        await super().stop()
        await record_cleanup(self.id, "stop")

    async def kill(self) -> None:
        emit("cleanup-entered", identity=self.id, method="kill")
        await super().kill()
        await record_cleanup(self.id, "kill")


class CheckpointBrowser:
    def __init__(self, identity: str):
        self.id = identity

    async def stop(self) -> None:
        emit("cleanup-entered", identity=self.id, method="stop")
        await record_cleanup(self.id, "stop")

    async def kill(self) -> None:
        await record_cleanup(self.id, "kill")


def create_browser():
    global COUNTER
    COUNTER += 1
    identity = f"probe-{COUNTER}"
    if not BROWSER:
        return CheckpointBrowser(identity)
    return browser_manager.create_browser_session(
        {
            "id": identity,
            "executable_path": BROWSER,
            "headless": True,
            "use_cloud": False,
            "cdp_url": None,
            "user_data_dir": WORKSPACE / identity,
            "allowed_domains": ["127.0.0.1", "localhost"],
            "enable_default_extensions": False,
            "disable_security": False,
        }
    )


class History:
    def final_result(self) -> str:
        return "offline fixture complete"


class OfflineAgent:
    """Replace model decisions only; use the real request and browser lifecycle."""

    def __init__(self, task, browser_session, **kwargs):
        self.task = task
        self.browser = browser_session

    async def run(self, **kwargs):
        if BROWSER:
            await self.browser.start()
            await self.browser.navigate_to(os.environ["MCP_COMPAT_URL"])
            screenshot = await self.browser.take_screenshot()
            if not screenshot:
                raise RuntimeError("real browser produced no screenshot")
            OWNED[self.browser.id] = [
                {"pid": process.pid, "created": process.create_time()}
                for process in psutil.Process().children(recursive=True)
            ]
            if not OWNED[self.browser.id]:
                raise RuntimeError("no owned browser process was observed")
        emit(
            "run-started",
            task=self.task,
            identity=self.browser.id,
            processes=OWNED.get(self.browser.id, []),
        )
        if self.task == "block":
            await anyio.sleep_forever()
        return History()


if __name__ == "__main__":
    if os.environ.get("BROWSER_USE_OFFLINE") != "1":
        raise RuntimeError("offline probe requires BROWSER_USE_OFFLINE=1")
    emit("server-started", pid=os.getpid(), created=psutil.Process().create_time())
    # Observe cleanup on the same factory-created session the application uses.
    browser_manager.BrowserSession = ObservedBrowser
    server.get_llm_model = lambda *args, **kwargs: object()
    server.create_browser_session = create_browser
    server.Agent = OfflineAgent
    server.launch_mcp_browser_use_server()
