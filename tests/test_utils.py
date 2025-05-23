import sys
import types
import importlib
import importlib.util
import os
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


def test_get_llm_model_returns_chatopenai():
    model = utils.get_llm_model('openai')
    assert isinstance(model, utils.ChatOpenAI)


def test_get_llm_model_unknown_provider_raises():
    with pytest.raises(ValueError):
        utils.get_llm_model('unknown')
