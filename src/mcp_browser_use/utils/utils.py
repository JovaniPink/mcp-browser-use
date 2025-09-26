# -*- coding: utf-8 -*-

import base64
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI

logger = logging.getLogger(__name__)


def get_llm_model(provider: str, **kwargs) -> Any:
    """
    Return an initialized language model client based on the given provider name.

    :param provider: The name of the LLM provider (e.g., "anthropic", "openai", "azure_openai").
    :param kwargs: Additional parameters (model_name, temperature, base_url, api_key, etc.).
    :return: An instance of a ChatLLM from the relevant langchain_* library.
    :raises ValueError: If the provider is unsupported.
    """
    if provider == "anthropic":
        base_url = kwargs.get("base_url") or "https://api.anthropic.com"
        api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        return ChatAnthropic(
            model_name=kwargs.get("model_name", "claude-3-5-sonnet-20240620"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )

    elif provider == "openai":
        base_url = kwargs.get("base_url") or os.getenv(
            "OPENAI_ENDPOINT", "https://api.openai.com/v1"
        )
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        return ChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )

    elif provider == "deepseek":
        base_url = kwargs.get("base_url") or os.getenv("DEEPSEEK_ENDPOINT", "")
        api_key = kwargs.get("api_key") or os.getenv("DEEPSEEK_API_KEY", "")
        return ChatOpenAI(
            model=kwargs.get("model_name", "deepseek-chat"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )

    elif provider == "gemini":
        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY", "")
        return ChatGoogleGenerativeAI(
            model=kwargs.get("model_name", "gemini-2.0-flash-exp"),
            temperature=kwargs.get("temperature", 0.0),
            google_api_key=api_key,
        )

    elif provider == "ollama":
        return ChatOllama(
            model=kwargs.get("model_name", "phi4"),
            temperature=kwargs.get("temperature", 0.0),
            num_ctx=128000,
            base_url=kwargs.get("base_url", "http://localhost:11434"),
        )

    elif provider == "azure_openai":
        base_url = kwargs.get("base_url") or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        api_key = kwargs.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY", "")
        return AzureChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            api_version="2024-05-01-preview",
            azure_endpoint=base_url,
            api_key=api_key,
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


# Commonly used model names for quick reference
model_names = {
    "anthropic": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
    "openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
    "deepseek": ["deepseek-chat"],
    "gemini": [
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash-thinking-exp",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b-latest",
        "gemini-2.0-flash-thinking-exp-1219",
    ],
    "ollama": ["deepseek-r1:671b", "qwen2.5:7b", "llama3.3", "phi4"],
    "azure_openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
}


def encode_image(img_path: Optional[str]) -> Optional[str]:
    """
    Convert an image at `img_path` into a base64-encoded string.
    Returns None if `img_path` is None or empty.
    Raises FileNotFoundError if the file doesn't exist.
    """
    if not img_path:
        return None

    try:
        with open(img_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        return image_data
    except FileNotFoundError as error:
        logger.error(f"Image not found at path {img_path}: {error}")
        raise
    except Exception as error:
        logger.error(f"Error encoding image at {img_path}: {error}")
        raise


def get_latest_files(
    directory: str, file_types: List[str] = [".webm", ".zip"]
) -> Dict[str, Optional[str]]:
    """
    Find the latest file for each extension in `file_types` under `directory`.
    Returns a dict {file_extension: latest_file_path or None}.

    :param directory: The directory to search.
    :param file_types: List of file extensions (e.g., [".webm", ".zip"]).
    :return: dict mapping each extension to the path of the newest file or None if not found.
    """
    latest_files: Dict[str, Optional[str]] = {ext: None for ext in file_types}

    if not os.path.exists(directory):
        logger.debug(f"Directory '{directory}' does not exist. Creating it.")
        os.makedirs(directory, exist_ok=True)
        return latest_files

    for file_type in file_types:
        try:
            matching_files = list(Path(directory).rglob(f"*{file_type}"))
            if matching_files:
                # Sort or use max() by modified time
                most_recent_file = max(matching_files, key=lambda path: path.stat().st_mtime)
                # Check if file is not actively being written
                if time.time() - most_recent_file.stat().st_mtime > 1.0:
                    latest_files[file_type] = str(most_recent_file)
                else:
                    logger.debug(
                        f"Skipping file {most_recent_file} - possibly still being written."
                    )
        except Exception as error:
            logger.error(
                f"Error getting latest {file_type} file in '{directory}': {error}"
            )

    return latest_files


async def capture_screenshot(browser_context) -> Optional[str]:
    """
    Capture a screenshot of the first open page (not 'about:blank') in the browser_context,
    returning a base64-encoded string, or None if no page is available.

    :param browser_context: The browser context which should hold a reference to the playwright browser.
    :return: Base64-encoded JPEG screenshot or None on failure.
    """
    playwright_browser = getattr(browser_context.browser, "playwright_browser", None)

    if not playwright_browser or not playwright_browser.contexts:
        logger.debug("No available playwright_browser or contexts.")
        return None

    # Use the first Playwright context
    playwright_context = playwright_browser.contexts[0]
    if not playwright_context:
        logger.debug("No valid playwright_context found.")
        return None

    # Find the first non-blank page
    browser_pages = playwright_context.pages
    if not browser_pages:
        logger.debug("No pages available in playwright_context.")
        return None

    active_page = next((page for page in browser_pages if page.url != "about:blank"), browser_pages[0])

    try:
        screenshot = await active_page.screenshot(type="jpeg", quality=75, scale="css")
        encoded_screenshot = base64.b64encode(screenshot).decode("utf-8")
        return encoded_screenshot
    except Exception as error:
        logger.error(f"Failed to capture screenshot: {error}")
        return None
