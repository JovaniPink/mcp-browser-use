"""Provider factory using browser-use's supported chat-model adapters."""

from __future__ import annotations

import os
from typing import Any

from browser_use import (
    ChatAnthropic,
    ChatAzureOpenAI,
    ChatBrowserUse,
    ChatGoogle,
    ChatOllama,
    ChatOpenAI,
)


def get_llm_model(
    provider: str,
    *,
    model_name: str,
    temperature: float = 0.3,
    base_url: str | None = None,
    api_key: str | None = None,
) -> Any:
    """Build a browser-use-native LLM adapter for a supported provider."""

    provider = provider.strip().lower()

    if provider == "browser_use":
        return ChatBrowserUse(
            model=model_name,
            api_key=api_key or os.getenv("BROWSER_USE_API_KEY"),
        )
    if provider == "anthropic":
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            base_url=base_url or os.getenv("ANTHROPIC_API_ENDPOINT"),
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )
    if provider == "openai":
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            base_url=base_url or os.getenv("OPENAI_ENDPOINT"),
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )
    if provider == "deepseek":
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            base_url=base_url
            or os.getenv("DEEPSEEK_ENDPOINT", "https://api.deepseek.com"),
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
        )
    if provider == "gemini":
        return ChatGoogle(
            model=model_name,
            temperature=temperature,
            api_key=api_key or os.getenv("GOOGLE_API_KEY"),
        )
    if provider == "ollama":
        return ChatOllama(
            model=model_name,
            host=base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )
    if provider == "azure_openai":
        return ChatAzureOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=base_url or os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )

    supported = "anthropic, azure_openai, browser_use, deepseek, gemini, ollama, openai"
    raise ValueError(f"Unsupported provider {provider!r}. Supported: {supported}.")
