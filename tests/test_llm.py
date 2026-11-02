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
