"""Static contracts for the local Smithery stdio launcher."""

from pathlib import Path

SMITHERY_CONFIG = Path(__file__).parents[1] / "smithery.yaml"


def _config_text() -> str:
    return SMITHERY_CONFIG.read_text(encoding="utf-8")


def test_smithery_uses_frozen_stdio_launch_without_implicit_cdp() -> None:
    config = _config_text()

    assert "args: ['run', '--frozen', 'mcp-browser-use']" in config
    assert "CHROME_DEBUGGING_PORT" not in config
    assert "CHROME_DEBUGGING_HOST" not in config


def test_smithery_maps_only_the_selected_provider_credentials() -> None:
    config = _config_text()

    for provider in (
        "anthropic",
        "azure_openai",
        "browser_use",
        "deepseek",
        "gemini",
        "ollama",
        "openai",
    ):
        assert f"          - {provider}\n" in config

    assert "modelApiKey" in config
    assert "keyNames[provider]" in config
    assert "openaiApiKey" not in config
    assert "anthropicApiKey" not in config


def test_smithery_requires_a_key_for_every_hosted_provider() -> None:
    config = _config_text()

    assert "not:\n                const: ollama" in config
    assert "then:\n          required:\n            - modelApiKey" in config
    assert "provider !== 'ollama' && !config.modelApiKey" in config
    assert "modelApiKey is required for non-Ollama providers" in config


def test_smithery_preserves_false_and_zero_values() -> None:
    config = _config_text()

    assert "config.mcpTemperature ?? 0.3" in config
    assert "config.mcpUseVision ?? true" in config
    assert "config.browserUseHeadless ?? true" in config
