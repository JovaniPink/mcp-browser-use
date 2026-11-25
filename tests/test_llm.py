from types import SimpleNamespace

import pytest

from mcp_browser_use.utils import llm as llm_module


class DummyModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.mark.parametrize(
    ("provider", "attribute"),
    (
        ("anthropic", "ChatAnthropic"),
        ("azure_openai", "ChatAzureOpenAI"),
        ("browser_use", "ChatBrowserUse"),
        ("deepseek", "ChatOpenAI"),
        ("gemini", "ChatGoogle"),
        ("ollama", "ChatOllama"),
        ("openai", "ChatOpenAI"),
    ),
)
def test_supported_provider_uses_browser_use_adapter(monkeypatch, provider, attribute):
    monkeypatch.setattr(llm_module, attribute, DummyModel)

    model = llm_module.get_llm_model(provider, model_name="test-model")

    assert isinstance(model, DummyModel)
    assert model.kwargs["model"] == "test-model"


def test_unknown_provider_fails_with_supported_values():
    with pytest.raises(ValueError, match="Unsupported provider"):
        llm_module.get_llm_model("unknown", model_name="test-model")


@pytest.mark.asyncio
@pytest.mark.parametrize("temperature", [None, 0.0, 0.7])
async def test_ollama_forwards_temperature_through_the_installed_adapter(
    monkeypatch, temperature
):
    calls = []

    class RecordingClient:
        async def chat(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(message=SimpleNamespace(content="completed"))

    model = llm_module.get_llm_model(
        "ollama",
        model_name="test-model",
        temperature=temperature,
        base_url="http://localhost:11435",
    )
    monkeypatch.setattr(model, "get_client", lambda: RecordingClient())

    result = await model.ainvoke([])

    assert model.host == "http://localhost:11435"
    assert result.completion == "completed"
    assert calls == [
        {
            "model": "test-model",
            "messages": [],
            "options": None if temperature is None else {"temperature": temperature},
        }
    ]
