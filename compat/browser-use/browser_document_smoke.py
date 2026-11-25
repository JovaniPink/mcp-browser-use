#!/usr/bin/env python3
"""Offline browser/document compatibility smoke, without LLM or harness IPC.

Run with the candidate interpreter. All browser navigation is to a loopback
fixture. For a container run, also use ``--network none`` and UID 10001.
The harness helper's CDP function is bridged to the real BrowserSession; its
daemon, IPC authentication, and ownership protocol are deliberately not tested.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import io
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from typing import Any, ClassVar

FIXTURE_TITLE = "MCP offline compatibility fixture"
FIXTURE_HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{FIXTURE_TITLE}</title>
<style>
body {{ margin: 0; background: white; font: 24px sans-serif; }}
header {{ height: 160px; background: #1256a1; color: white; padding: 32px;
          box-sizing: border-box; }}
h1 {{ margin: 0; font-size: 32px; }}
main {{ padding: 32px; }}
.panel {{ height: 900px; border: 4px solid #1256a1; padding: 24px; }}
</style></head><body>
<header><h1>{FIXTURE_TITLE}</h1></header>
<main><div class="panel">Local screenshot and document boundary probe.
<p id="marker">fixture-ready-20261125</p></div></main>
</body></html>""".encode()


def require(condition: bool, message: str) -> None:
    """Keep checks active even when Python is invoked with -O."""
    if not condition:
        raise RuntimeError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def configure_offline(work: Path, chromium: str) -> list[str]:
    """Configure package-local paths and deny Python non-loopback sockets."""
    os.environ.update(
        BROWSER_USE_OFFLINE="1",
        ANONYMIZED_TELEMETRY="false",
        BROWSER_USE_CLOUD_SYNC="false",
        BROWSER_USE_DISABLE_EXTENSIONS="1",
        BROWSER_USE_CONFIG_DIR=str(work / "browser-use-config"),
        BROWSER_USE_LOGGING_LEVEL="error",
        CHROME_PATH=chromium,
        BROWSER_USE_HEADLESS="true",
        BROWSER_USE_DISABLE_SECURITY="false",
        CHROME_PERSISTENT_SESSION="false",
        BH_HOME=str(work / "harness"),
        BH_AGENT_WORKSPACE=str(work / "harness-workspace"),
        BH_RUNTIME_DIR=str(work / "harness-runtime"),
        BH_TMP_DIR=str(work / "harness-tmp"),
        BH_OWNER="offline-compatibility-smoke",
        NO_PROXY="127.0.0.1,localhost,::1",
        no_proxy="127.0.0.1,localhost,::1",
    )
    # Isolate this child process from inherited proxy/provider configuration.
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "BROWSER_USE_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "BROWSER_USE_CDP_URL",
        "CHROME_DEBUGGING_HOST",
        "CHROME_DEBUGGING_PORT",
        "BROWSER_USE_PROXY_URL",
        "BROWSER_USE_PROXY_USERNAME",
        "BROWSER_USE_PROXY_PASSWORD",
        "BROWSER_USE_EXTRA_CHROMIUM_ARGS",
    ):
        os.environ.pop(name, None)

    denied: list[str] = []

    def is_loopback(host: Any) -> bool:
        if host in (None, "", "localhost", b"localhost"):
            return True
        if isinstance(host, bytes):
            host = host.decode("ascii")
        try:
            return ipaddress.ip_address(str(host).split("%", 1)[0]).is_loopback
        except ValueError:
            return False

    def audit(event: str, args: tuple[Any, ...]) -> None:
        host: Any = None
        if event == "socket.getaddrinfo":
            host = args[0]
        elif event in ("socket.connect", "socket.sendto"):
            sock, address = args
            if sock.family not in (socket.AF_INET, socket.AF_INET6):
                return
            host = address[0]
        else:
            return
        if not is_loopback(host):
            denied.append(f"{event}: non-loopback destination")
            raise PermissionError("Offline probe permits only loopback sockets")

    sys.addaudithook(audit)
    return denied


class LocalFixture(BaseHTTPRequestHandler):
    """Serve one page; also refuse all requests sent to the local proxy."""

    external_attempts: ClassVar[list[str]] = []
    fixture_requests: ClassVar[int] = 0

    def do_GET(self) -> None:
        if self.path == "/fixture":
            type(self).fixture_requests += 1
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(FIXTURE_HTML)))
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'",
            )
            self.end_headers()
            self.wfile.write(FIXTURE_HTML)
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            if self.path.startswith(("http://", "https://")):
                type(self).external_attempts.append("blocked HTTP proxy request")
            self.send_error(403, "Offline fixture only")

    def do_CONNECT(self) -> None:
        type(self).external_attempts.append("blocked HTTPS proxy tunnel")
        self.send_error(403, "Offline fixture only")

    def log_message(self, format: str, *args: Any) -> None:
        return


async def probe_document(work: Path) -> dict[str, Any]:
    """Exercise a real ReportLab PDF through the browser-use filesystem reader."""
    from browser_use.filesystem.file_system import FileSystem
    from pypdf import PdfReader
    from reportlab.pdfgen import canvas

    # ReportLab creates real PDF bytes; the application path reads them via pypdf.
    pdf_path = work / "multipage.pdf"
    markers = ["PAGE_ALPHA_001", "PAGE_BETA_002", "PAGE_GAMMA_003"]
    pdf = canvas.Canvas(str(pdf_path), pagesize=(612, 792), invariant=1)
    for index, marker in enumerate(markers, 1):
        pdf.drawString(72, 720, marker)
        pdf.drawString(72, 690, f"Offline compatibility page {index} of 3.")
        pdf.showPage()
    pdf.save()
    reader = PdfReader(str(pdf_path))
    require(len(reader.pages) == 3, "Generated PDF does not have three pages")
    fs = FileSystem(work / "agent-files", create_default_files=False)
    structured = await fs.read_file_structured(str(pdf_path), external_file=True)
    message = structured["message"]
    for index, marker in enumerate(markers, 1):
        require(marker in message, f"FileSystem PDF extraction lost {marker}")
        require(f"--- Page {index} ---" in message, "Missing PDF page boundary")
    require("3 pages" in message, "FileSystem PDF count was not preserved")
    require(structured["images"] is None, "Unexpected PDF image return value")
    (work / "pdf-extracted.txt").write_text(message, encoding="utf-8")
    return {
        "pages": 3,
        "all_page_markers": True,
        "reader": "FileSystem.read_file_structured(external_file=True)",
        "bytes": pdf_path.stat().st_size,
        "sha256": sha256(pdf_path.read_bytes()),
    }


async def probe(work: Path, chromium: str, denied: list[str]) -> dict[str, Any]:
    # Import after offline settings and isolated filesystem paths are installed.
    from browser_use.screenshots.service import ScreenshotService
    from PIL import Image

    from mcp_browser_use.browser.browser_manager import create_browser_session

    report: dict[str, Any] = {
        "status": "running",
        "uid": os.getuid() if hasattr(os, "getuid") else None,
        "python": sys.version.split()[0],
        "versions": {
            name: version(name)
            for name in (
                "browser-use",
                "browser-harness",
                "pillow",
                "pypdf",
                "reportlab",
                "anyio",
                "cdp-use",
            )
        },
        "offline": {
            "browser_use_offline": True,
            "telemetry": False,
            "cloud_sync": False,
            "default_extensions": False,
            "python_loopback_guard": True,
            "chromium_nonlocal_proxy": "local deny-only endpoint",
        },
        "scope": {
            "real_browser_session": True,
            "provider_calls": False,
            "cloud_browser": False,
            "harness_ipc": False,
            "harness_transport": "real BrowserSession CDP bridge",
            "llm_agent_loop": False,
            "container_uid_10001": os.getuid() == 10001,
            "browser_launch": "mcp_browser_use.create_browser_session",
            "chromium_sandbox": False,
            "sandbox_scope": (
                "explicit container-compatible setting, not sandbox validation"
            ),
        },
        "checks": {},
    }

    report["checks"]["pdf"] = await probe_document(work)
    report["chromium"] = (
        await asyncio.to_thread(
            subprocess.check_output, [chromium, "--version"], text=True, timeout=10
        )
    ).strip()

    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalFixture)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    browser = create_browser_session(
        overrides={
            "use_cloud": False,
            "is_local": True,
            "cdp_url": None,
            "proxy": None,
            "chromium_sandbox": False,
            "enable_default_extensions": False,
            "captcha_solver": False,
            "keep_alive": False,
            "user_data_dir": str(work / "chromium-profile"),
            "downloads_path": str(work / "downloads"),
            "allowed_domains": ["127.0.0.1"],
            "viewport": {"width": 1600, "height": 900},
            "no_viewport": False,
            "device_scale_factor": 1,
            "args": [
                "--disable-background-networking",
                "--disable-component-update",
                "--disable-domain-reliability",
                "--disable-sync",
                "--disable-quic",
                "--dns-prefetch-disable",
                "--no-first-run",
                "--no-default-browser-check",
                f"--proxy-server={origin}",
                "--proxy-bypass-list=127.0.0.1;localhost;[::1]",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost",
            ],
        }
    )
    require(browser.browser_profile.headless is True, "App lost headless environment")
    require(
        str(browser.browser_profile.executable_path) == chromium,
        "App lost CHROME_PATH environment",
    )
    try:
        await asyncio.wait_for(browser.start(), timeout=30)
        await asyncio.wait_for(browser.navigate_to(origin + "/fixture"), timeout=20)
        page = await browser.get_current_page()
        require(page is not None, "BrowserSession has no current page")
        title = await page.evaluate("() => document.title")
        marker = await page.evaluate(
            "() => document.getElementById('marker').textContent"
        )
        require(title == FIXTURE_TITLE, "Local fixture title did not load")
        require(marker == "fixture-ready-20261125", "Local fixture marker missing")

        screenshot_path = work / "browser-session.png"
        png = await browser.take_screenshot(path=str(screenshot_path))
        require(png.startswith(b"\x89PNG\r\n\x1a\n"), "Not a real PNG screenshot")
        require(screenshot_path.read_bytes() == png, "Screenshot bytes differ on disk")
        with Image.open(io.BytesIO(png)) as image:
            image.load()
            require(image.size == (1600, 900), "Unexpected screenshot dimensions")
            require(
                image.convert("RGB").getpixel((10, 10)) == (18, 86, 161),
                "Screenshot does not show the fixture's colored header",
            )
            resized = image.resize((400, 225), Image.Resampling.LANCZOS)
            resized.save(work / "pillow-resized.png")
        with Image.open(work / "pillow-resized.png") as image:
            image.load()
            require(image.size == (400, 225), "Pillow resize failed")
        report["checks"]["browser"] = {
            "title": title,
            "navigation": "loopback HTTP fixture",
            "png_dimensions": [1600, 900],
            "fixture_pixel_verified": True,
            "png_sha256": sha256(png),
        }
        report["checks"]["pillow_resize"] = {
            "dimensions": [400, 225],
            "resampling": "LANCZOS",
        }

        screenshot_service = ScreenshotService(work / "screenshot-service")
        stored = await screenshot_service.store_screenshot(
            base64.b64encode(png).decode("ascii"), step_number=1
        )
        loaded = await screenshot_service.get_screenshot(stored)
        require(loaded is not None, "ScreenshotService returned no screenshot")
        require(
            base64.b64decode(loaded) == png, "AnyIO screenshot roundtrip changed bytes"
        )
        report["checks"]["screenshot_service"] = {
            "anyio_write_read": True,
            "byte_identical": True,
        }

        # Exercise the real harness helper without a daemon or an IPC session.
        from browser_harness import helpers

        cdp_session = await browser.get_or_create_cdp_session()
        loop = asyncio.get_running_loop()
        calls: list[str] = []

        async def real_capture(params: dict[str, Any]) -> dict[str, Any]:
            return await cdp_session.cdp_client.send.Page.captureScreenshot(
                params=params, session_id=cdp_session.session_id
            )

        def cdp_bridge(
            method: str,
            session_id: str | None = None,
            _response_timeout: float | None = None,
            **params: Any,
        ) -> dict[str, Any]:
            require(method == "Page.captureScreenshot", "Unexpected harness CDP call")
            require(session_id is None, "Unexpected harness session override")
            calls.append(method)
            future = asyncio.run_coroutine_threadsafe(real_capture(params), loop)
            return future.result(timeout=min(_response_timeout or 20, 20))

        old_cdp = helpers.cdp
        helpers.cdp = cdp_bridge
        try:
            harness_path = await asyncio.to_thread(
                helpers.capture_screenshot,
                str(work / "harness-max-dim.png"),
                False,
                640,
            )
        finally:
            helpers.cdp = old_cdp
        with Image.open(harness_path) as image:
            image.load()
            require(image.size == (640, 360), "Harness max_dim resize failed")
            require(
                image.convert("RGB").getpixel((4, 4)) == (18, 86, 161),
                "Harness screenshot does not contain the real fixture",
            )
        require(calls == ["Page.captureScreenshot"], "Harness bypassed the CDP bridge")
        report["checks"]["harness_screenshot"] = {
            "real_cdp_calls": len(calls),
            "max_dim": 640,
            "dimensions": [640, 360],
            "daemon_ipc_exercised": False,
        }
    finally:
        try:
            await asyncio.wait_for(browser.kill(), timeout=20)
        finally:
            await asyncio.to_thread(server.shutdown)
            server.server_close()
            thread.join(timeout=2)

    require(not denied, "A Python dependency attempted a non-loopback connection")
    require(LocalFixture.fixture_requests > 0, "No real HTTP fixture request observed")
    report["offline"]["python_nonloopback_attempts"] = len(denied)
    report["offline"]["blocked_chromium_proxy_attempts"] = len(
        LocalFixture.external_attempts
    )
    report["checks"]["cleanup"] = {"browser_kill_completed": True}
    report["status"] = "pass"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", default=shutil.which("chromium"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    require(bool(args.chromium), "Chromium must already be installed")
    with tempfile.TemporaryDirectory(prefix="mcp-browser-document-smoke-") as temp:
        work = Path(temp)
        denied = configure_offline(work, args.chromium)
        report = asyncio.run(asyncio.wait_for(probe(work, args.chromium, denied), 90))
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            for name in (
                "browser-session.png",
                "pillow-resized.png",
                "harness-max-dim.png",
                "multipage.pdf",
                "pdf-extracted.txt",
            ):
                shutil.copy2(work / name, args.output_dir / name)
            (args.output_dir / "receipt.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
