import base64
import importlib
import importlib.util
import os
import sys
import time
import types

import pytest

# Path to utils module
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UTILS_PATH = os.path.join(ROOT, "src", "mcp_browser_use", "utils", "utils.py")

# Provide dummy langchain modules if they are not installed
if "langchain_openai" not in sys.modules:
    module = types.ModuleType("langchain_openai")

    class ChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    class AzureChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    module.ChatOpenAI = ChatOpenAI
    module.AzureChatOpenAI = AzureChatOpenAI
    sys.modules["langchain_openai"] = module

if "langchain_anthropic" not in sys.modules:
    module = types.ModuleType("langchain_anthropic")

    class ChatAnthropic:
        def __init__(self, *args, **kwargs):
            pass

    module.ChatAnthropic = ChatAnthropic
    sys.modules["langchain_anthropic"] = module

if "langchain_google_genai" not in sys.modules:
    module = types.ModuleType("langchain_google_genai")

    class ChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs):
            pass

    module.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    sys.modules["langchain_google_genai"] = module

if "langchain_ollama" not in sys.modules:
    module = types.ModuleType("langchain_ollama")

    class ChatOllama:
        def __init__(self, *args, **kwargs):
            pass

    module.ChatOllama = ChatOllama
    sys.modules["langchain_ollama"] = module

if "browser_use" not in sys.modules:
    browser_use_module = types.ModuleType("browser_use")
    browser_module = types.ModuleType("browser_use.browser")
    events_module = types.ModuleType("browser_use.browser.events")

    class ScreenshotEvent:
        def __init__(self, full_page: bool = False):
            self.full_page = full_page

    events_module.ScreenshotEvent = ScreenshotEvent
    browser_module.events = events_module
    browser_use_module.browser = browser_module

    sys.modules["browser_use"] = browser_use_module
    sys.modules["browser_use.browser"] = browser_module
    sys.modules["browser_use.browser.events"] = events_module

# Import utils module directly from file after stubbing dependencies
spec = importlib.util.spec_from_file_location("mcp_browser_use.utils.utils", UTILS_PATH)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_get_llm_model_returns_chatopenai():
    model = utils.get_llm_model("openai")
    assert isinstance(model, utils.ChatOpenAI)


def test_get_llm_model_unknown_provider_raises():
    with pytest.raises(ValueError):
        utils.get_llm_model("unknown")


def test_encode_image_handles_empty_path():
    assert utils.encode_image(None) is None
    assert utils.encode_image("") is None


def test_encode_image_roundtrip(tmp_path):
    image_path = tmp_path / "image.bin"
    payload = b"test-bytes"
    image_path.write_bytes(payload)

    encoded = utils.encode_image(str(image_path))

    assert encoded == base64.b64encode(payload).decode("utf-8")


def test_encode_image_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        utils.encode_image(str(tmp_path / "missing.bin"))


def test_get_latest_files_creates_directory(tmp_path):
    target = tmp_path / "captures"

    result = utils.get_latest_files(str(target), file_types=[".webm", ".zip"])

    assert target.exists()
    assert result == {".webm": None, ".zip": None}


def test_get_latest_files_skips_recent_files(tmp_path, monkeypatch):
    directory = tmp_path / "captures"
    directory.mkdir()

    recent_path = directory / "recent.webm"
    recent_path.write_text("recent")

    now = time.time()
    os.utime(recent_path, (now, now))

    monkeypatch.setattr(utils.time, "time", lambda: now)

    result = utils.get_latest_files(str(directory), file_types=[".webm"])

    assert result == {".webm": None}


@pytest.mark.anyio("asyncio")
async def test_capture_screenshot_uses_event_bus():
    screenshot_payload = base64.b64encode(b"payload").decode("utf-8")

    class DummyEvent:
        def __init__(self, result):
            self._result = result
            self.awaited = False

        def __await__(self):
            async def _wait():
                self.awaited = True
                return self

            return _wait().__await__()

        async def event_result(self, raise_if_any=True, raise_if_none=True):
            return self._result

    class DummyEventBus:
        def __init__(self, dispatched_event):
            self._event = dispatched_event
            self.dispatched = []

        def dispatch(self, event):
            self.dispatched.append(event)
            return self._event

    class DummyBrowserSession:
        def __init__(self, event_bus):
            self.event_bus = event_bus

    dummy_event = DummyEvent(screenshot_payload)
    event_bus = DummyEventBus(dummy_event)
    session = DummyBrowserSession(event_bus)

    encoded = await utils.capture_screenshot(session)

    assert encoded == screenshot_payload
    assert dummy_event.awaited is True
    assert len(event_bus.dispatched) == 1
    assert isinstance(event_bus.dispatched[0], utils.ScreenshotEvent)


@pytest.mark.anyio("asyncio")
async def test_capture_screenshot_returns_none_on_error():
    class DummyErrorEvent:
        def __await__(self):
            async def _wait():
                return self

            return _wait().__await__()

        async def event_result(self, raise_if_any=True, raise_if_none=True):
            raise RuntimeError("boom")

    class DummyEventBus:
        def dispatch(self, event):
            return DummyErrorEvent()

    class DummyBrowserSession:
        def __init__(self):
            self.event_bus = DummyEventBus()

    session = DummyBrowserSession()

    result = await utils.capture_screenshot(session)

    assert result is None
