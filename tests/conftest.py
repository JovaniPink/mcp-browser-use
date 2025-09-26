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

