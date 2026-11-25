"""Exercise real MCP subprocess startup, cancellation, disconnect, and reuse."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psutil
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = (
            b"<html><title>Offline MCP fixture</title>"
            b"<body>Owned browser fixture</body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass


def records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


async def wait_record(path: Path, kind: str, count: int = 1) -> dict:
    async with asyncio.timeout(30):
        while True:
            found = [item for item in records(path) if item["kind"] == kind]
            if len(found) >= count:
                return found[count - 1]
            await asyncio.sleep(0.02)


def process_alive(item: dict) -> bool:
    try:
        process = psutil.Process(item["pid"])
        return (
            process.create_time() == item["created"]
            and process.is_running()
            and process.status() != psutil.STATUS_ZOMBIE
        )
    except psutil.NoSuchProcess:
        return False


async def assert_processes_exited(path: Path) -> dict:
    items = records(path)
    owned = [process for item in items for process in item.get("processes", [])]
    servers = [item for item in items if item["kind"] == "server-started"]
    async with asyncio.timeout(10):
        while any(process_alive(item) for item in [*owned, *servers]):
            await asyncio.sleep(0.02)
    return {
        "owned_browser_pids_exited": sorted({item["pid"] for item in owned}),
        "server_pids_exited": sorted({item["pid"] for item in servers}),
        "pid_creation_times_checked": True,
    }


def base_environment() -> dict[str, str]:
    # StdioTransport inherits the SDK's small OS-variable allowlist. No provider
    # keys or user browser/session settings are forwarded by this probe.
    return {
        "BROWSER_USE_OFFLINE": "1",
        "ANONYMIZED_TELEMETRY": "false",
        "BROWSER_USE_SETUP_LOGGING": "false",
        "MCP_MAX_CONCURRENT_RUNS": "1",
    }


async def installed_entrypoint(mode: str, directory: Path) -> None:
    executable = Path(sys.executable).parent / "mcp-browser-use"
    transport = StdioTransport(
        command=str(executable),
        args=[],
        env=base_environment(),
        cwd=str(directory),
        keep_alive=False,
        log_file=directory / f"entrypoint-{mode}.log",
    )
    async with Client(transport, mode=mode, timeout=15) as client:
        tools = await client.list_tools()
        assert [tool.name for tool in tools] == ["run_browser_agent"]
        assert tools[0].input_schema["required"] == ["task"]
        try:
            await client.call_tool("run_browser_agent", {"task": " "})
        except ToolError as error:
            assert "task must not be empty" in str(error)
        else:
            raise AssertionError("empty task allocated a provider/browser")


def fixture_transport(
    directory: Path, browser: str | None, url: str
) -> tuple[StdioTransport, Path]:
    directory.mkdir()
    events = directory / "events.jsonl"
    environment = base_environment() | {
        "MCP_COMPAT_EVENTS": str(events),
        "MCP_COMPAT_WORKSPACE": str(directory),
        "MCP_COMPAT_URL": url,
    }
    if browser:
        environment["MCP_COMPAT_BROWSER"] = browser
    transport = StdioTransport(
        command=sys.executable,
        args=[str(Path(__file__).with_name("mcp_transport_fixture.py"))],
        env=environment,
        cwd=str(directory),
        keep_alive=False,
        log_file=directory / "server.log",
    )
    return transport, events


async def cancellation_and_reuse(
    mode: str, directory: Path, browser: str | None, url: str
) -> dict:
    transport, events = fixture_transport(directory, browser, url)
    async with Client(transport, mode=mode, timeout=60) as client:
        pending = asyncio.create_task(
            client.call_tool("run_browser_agent", {"task": "block"})
        )
        await wait_record(events, "run-started")
        pending.cancel()
        try:
            await pending
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("cancelled client request returned success")
        cleanup = await wait_record(events, "cleanup-complete")
        assert cleanup["alive"] == [], cleanup
        result = await client.call_tool("run_browser_agent", {"task": "complete"})
        assert result.data == "offline fixture complete"
        cleanup = await wait_record(events, "cleanup-complete", count=2)
        assert cleanup["alive"] == [], cleanup
    seen = records(events)
    first_cleanup = next(
        i for i, item in enumerate(seen) if item["kind"] == "cleanup-complete"
    )
    second_start = next(
        i
        for i, item in enumerate(seen)
        if item["kind"] == "run-started" and item["task"] == "complete"
    )
    assert first_cleanup < second_start
    return {
        "cancelled_request": "passed",
        "subsequent_request": "passed",
        "process_exit": await assert_processes_exited(events),
    }


async def disconnect(mode: str, directory: Path, browser: str | None, url: str) -> dict:
    transport, events = fixture_transport(directory, browser, url)
    async with Client(transport, mode=mode, timeout=60) as client:
        pending = asyncio.create_task(
            client.call_tool("run_browser_agent", {"task": "block"})
        )
        await wait_record(events, "run-started")
        # Exiting closes the real stdio connection with an in-flight request.
    outcome = await asyncio.gather(pending, return_exceptions=True)
    assert isinstance(outcome[0], BaseException), outcome
    cleanup = await wait_record(events, "cleanup-complete")
    assert cleanup["alive"] == [], cleanup
    return {
        "disconnect": "passed",
        "process_exit": await assert_processes_exited(events),
    }


async def run(browser: str | None) -> dict:
    if browser:
        subprocess.run([browser, "--version"], check=True)
    http = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="mcbu-mcp-compat-") as temporary:
            directory = Path(temporary)
            url = f"http://127.0.0.1:{http.server_port}/fixture"
            results = {}
            try:
                for mode in ("auto", "legacy"):
                    await installed_entrypoint(mode, directory)
                    results[mode] = {
                        "installed_entrypoint": "passed",
                        "cancellation_and_reuse": await cancellation_and_reuse(
                            mode, directory / f"cancel-{mode}", browser, url
                        ),
                        "disconnect": await disconnect(
                            mode, directory / f"disconnect-{mode}", browser, url
                        ),
                    }
            except BaseException:
                for log in sorted(directory.rglob("*.log")):
                    print(
                        f"Fixture log: {log.name}\n{log.read_text()[-6000:]}",
                        file=sys.stderr,
                    )
                for event_file in sorted(directory.rglob("events.jsonl")):
                    print(event_file.read_text(), file=sys.stderr)
                raise
            return {
                "backend": "real local Chromium"
                if browser
                else "checkpoint-only lifecycle fixture",
                "uid": os.getuid(),
                "modes": results,
            }
    finally:
        http.shutdown()
        thread.join()
        http.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--browser-executable")
    selection.add_argument("--checkpoint-only", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(asyncio.run(run(arguments.browser_executable)), indent=2))
