"""Test fixtures and environment setup for the test suite."""

import importlib
import os
import sys
import types

BASE_DIR = os.path.dirname(__file__)
STUBS_DIR = os.path.join(BASE_DIR, "stubs")
SRC_DIR = os.path.join(os.path.dirname(BASE_DIR), "src")

for path in (STUBS_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

if "langchain_openai" not in sys.modules:
    importlib.import_module("langchain_openai")

if "langchain_anthropic" not in sys.modules:
    module = types.ModuleType("langchain_anthropic")

    class ChatAnthropic:  # type: ignore[too-many-ancestors]
        def __init__(self, *args, **kwargs):
            pass

    module.ChatAnthropic = ChatAnthropic
    sys.modules["langchain_anthropic"] = module

if "langchain_google_genai" not in sys.modules:
    module = types.ModuleType("langchain_google_genai")

    class ChatGoogleGenerativeAI:  # type: ignore[too-many-ancestors]
        def __init__(self, *args, **kwargs):
            pass

    module.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    sys.modules["langchain_google_genai"] = module

if "langchain_ollama" not in sys.modules:
    module = types.ModuleType("langchain_ollama")

    class ChatOllama:  # type: ignore[too-many-ancestors]
        def __init__(self, *args, **kwargs):
            pass

    module.ChatOllama = ChatOllama
    sys.modules["langchain_ollama"] = module

if "playwright" not in sys.modules:
    playwright_module = types.ModuleType("playwright")
    async_api_module = types.ModuleType("playwright.async_api")

    class Browser:
        async def close(self):
            pass

    class BrowserContext:
        async def close(self):
            pass

    class Playwright:
        class Chromium:
            async def connect(self, *args, **kwargs):
                return Browser()

            async def connect_over_cdp(self, *args, **kwargs):
                return Browser()

            async def launch(self, *args, **kwargs):
                return Browser()

        def __init__(self):
            self.chromium = Playwright.Chromium()

    async def async_playwright():
        class Manager:
            async def __aenter__(self):
                return Playwright()

            async def __aexit__(self, exc_type, exc, tb):
                pass

        return Manager()

    async_api_module.Browser = Browser
    async_api_module.BrowserContext = BrowserContext
    async_api_module.Playwright = Playwright
    async_api_module.async_playwright = async_playwright

    playwright_module.async_api = async_api_module
    sys.modules["playwright"] = playwright_module
    sys.modules["playwright.async_api"] = async_api_module
