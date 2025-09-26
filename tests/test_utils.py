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
if 'langchain_openai' not in sys.modules:
    module = types.ModuleType('langchain_openai')
    class ChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass
    class AzureChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass
    module.ChatOpenAI = ChatOpenAI
    module.AzureChatOpenAI = AzureChatOpenAI
    sys.modules['langchain_openai'] = module

if 'langchain_anthropic' not in sys.modules:
    module = types.ModuleType('langchain_anthropic')
    class ChatAnthropic:
        def __init__(self, *args, **kwargs):
            pass
    module.ChatAnthropic = ChatAnthropic
    sys.modules['langchain_anthropic'] = module

if 'langchain_google_genai' not in sys.modules:
    module = types.ModuleType('langchain_google_genai')
    class ChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs):
            pass
    module.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    sys.modules['langchain_google_genai'] = module

if 'langchain_ollama' not in sys.modules:
    module = types.ModuleType('langchain_ollama')
    class ChatOllama:
        def __init__(self, *args, **kwargs):
            pass
    module.ChatOllama = ChatOllama
    sys.modules['langchain_ollama'] = module

# Import utils module directly from file after stubbing dependencies
spec = importlib.util.spec_from_file_location(
    'mcp_browser_use.utils.utils', UTILS_PATH
)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_get_llm_model_returns_chatopenai():
    model = utils.get_llm_model('openai')
    assert isinstance(model, utils.ChatOpenAI)


def test_get_llm_model_unknown_provider_raises():
    with pytest.raises(ValueError):
        utils.get_llm_model('unknown')


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
async def test_capture_screenshot_prefers_non_blank_page():
    class DummyPage:
        def __init__(self, url, payload):
            self.url = url
            self._payload = payload
            self.calls = 0

        async def screenshot(self, **kwargs):
            self.calls += 1
            return self._payload

    class DummyPlaywrightContext:
        def __init__(self, pages):
            self.pages = pages

    class DummyPlaywrightBrowser:
        def __init__(self, contexts):
            self.contexts = contexts

    class DummyBrowser:
        def __init__(self, contexts):
            self.playwright_browser = DummyPlaywrightBrowser(contexts)

    class DummyBrowserContext:
        def __init__(self, contexts):
            self.browser = DummyBrowser(contexts)

    blank_page = DummyPage("about:blank", b"blank")
    active_page = DummyPage("https://example.com", b"payload")
    browser_context = DummyBrowserContext([DummyPlaywrightContext([blank_page, active_page])])

    encoded = await utils.capture_screenshot(browser_context)

    assert encoded == base64.b64encode(b"payload").decode("utf-8")
    assert blank_page.calls == 0
    assert active_page.calls == 1


@pytest.mark.anyio("asyncio")
async def test_capture_screenshot_returns_none_on_error():
    class FailingPage:
        url = "https://example.com"

        async def screenshot(self, **kwargs):
            raise RuntimeError("boom")

    class DummyPlaywrightContext:
        def __init__(self, pages):
            self.pages = pages

    class DummyPlaywrightBrowser:
        def __init__(self, contexts):
            self.contexts = contexts

    class DummyBrowser:
        def __init__(self, contexts):
            self.playwright_browser = DummyPlaywrightBrowser(contexts)

    class DummyBrowserContext:
        def __init__(self, contexts):
            self.browser = DummyBrowser(contexts)

    browser_context = DummyBrowserContext([DummyPlaywrightContext([FailingPage()])])

    result = await utils.capture_screenshot(browser_context)

    assert result is None
