# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import traceback
import logging
from typing import Any, Optional

from browser_use.browser.profile import ProxySettings
from fastmcp import FastMCP
from mcp_browser_use.agent.custom_agent import CustomAgent
from mcp_browser_use.controller.custom_controller import CustomController
from mcp_browser_use.browser.custom_browser import CustomBrowser
from mcp_browser_use.utils import utils
from mcp_browser_use.utils.agent_state import AgentState

# Configure logging for the entire module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global references for single "running agent" approach
_global_agent: Optional[CustomAgent] = None
_global_browser: Optional[CustomBrowser] = None
_global_page: Any | None = None
_global_agent_state: AgentState = AgentState()

app = FastMCP("mcp_browser_use")


async def _cleanup_browser_resources() -> None:
    """
    Safely clean up browser resources and reset global references.
    Any exceptions are logged and swallowed to ensure we attempt
    as much cleanup as possible.

    Need to add types.
    """
    global _global_browser, _global_page, _global_agent_state, _global_agent

    try:
        if _global_agent_state:
            try:
                _global_agent_state.request_stop()
            except Exception as stop_error:
                logger.warning("Error stopping agent state: %s", stop_error)

        if _global_page:
            try:
                close = getattr(_global_page, "close", None)
                if close:
                    await close()
            except Exception as page_error:
                logger.warning("Error closing browser page: %s", page_error)

        if _global_browser:
            try:
                await _global_browser.stop()
            except Exception as browser_error:
                logger.warning("Error stopping browser: %s", browser_error)

    except Exception as e:
        # Log the error, but don't re-raise
        logger.error("Unexpected error during browser cleanup: %s", e)
    finally:
        # Reset global variables
        _global_browser = None
        _global_page = None
        _global_agent_state = AgentState()
        _global_agent = None


@app.tool()
async def run_browser_agent(task: str, add_infos: str = "") -> str:
    """
    This is the entrypoint for running a browser-based agent.

    :param task: The main instruction or goal for the agent.
    :param add_infos: Additional information or context for the agent.
    :return: The final result string from the agent run.
    """
    global _global_agent, _global_browser, _global_page, _global_agent_state

    try:
        # Clear any previous agent stop signals
        _global_agent_state.clear_stop()

        # Read environment variables with defaults and parse carefully
        # Fallback to defaults if parsing fails.
        model_provider = os.getenv("MCP_MODEL_PROVIDER", "anthropic")
        model_name = os.getenv("MCP_MODEL_NAME", "claude-3-5-sonnet-20241022")

        def safe_float(env_var: str, default: float) -> float:
            """Safely parse a float from an environment variable."""
            try:
                return float(os.getenv(env_var, str(default)))
            except ValueError:
                logger.warning(f"Invalid float for {env_var}, using default={default}")
                return default

        def safe_int(env_var: str, default: int) -> int:
            """Safely parse an int from an environment variable."""
            try:
                return int(os.getenv(env_var, str(default)))
            except ValueError:
                logger.warning(f"Invalid int for {env_var}, using default={default}")
                return default

        # Get environment variables with defaults
        temperature = safe_float("MCP_TEMPERATURE", 0.3)
        max_steps = safe_int("MCP_MAX_STEPS", 30)
        use_vision = os.getenv("MCP_USE_VISION", "true").lower() == "true"
        max_actions_per_step = safe_int("MCP_MAX_ACTIONS_PER_STEP", 5)
        tool_call_in_content = (
            os.getenv("MCP_TOOL_CALL_IN_CONTENT", "true").lower() == "true"
        )

        # Prepare LLM
        llm = utils.get_llm_model(
            provider=model_provider, model_name=model_name, temperature=temperature
        )

        # Get path to the Chrome/Chromium binary if provided
        chrome_path = os.getenv("CHROME_PATH") or None

        # Determine headless mode with backward-compatible defaults
        headless_env = os.getenv("BROWSER_USE_HEADLESS", "false").lower()
        headless = headless_env in {"1", "true", "yes", "on"}

        # Optional proxy configuration
        proxy_settings: ProxySettings | None = None
        proxy_url = os.getenv("BROWSER_USE_PROXY_URL")
        if proxy_url:
            proxy_settings = ProxySettings(
                server=proxy_url,
                bypass=os.getenv("BROWSER_USE_NO_PROXY"),
                username=os.getenv("BROWSER_USE_PROXY_USERNAME"),
                password=os.getenv("BROWSER_USE_PROXY_PASSWORD"),
            )

        allowed_domains_env = os.getenv("BROWSER_USE_ALLOWED_DOMAINS")
        allowed_domains = None
        if allowed_domains_env:
            allowed_domains = [
                domain.strip()
                for domain in allowed_domains_env.split(",")
                if domain.strip()
            ]

        extra_args_env = os.getenv("BROWSER_USE_EXTRA_CHROMIUM_ARGS")
        extra_args = None
        if extra_args_env:
            extra_args = [
                arg.strip()
                for arg in extra_args_env.split(",")
                if arg.strip()
            ]

        cdp_url = os.getenv("BROWSER_USE_CDP_URL") or None

        # Create or reuse the global browser
        if not _global_browser:
            _global_browser = CustomBrowser(
                headless=headless,
                disable_security=os.getenv("BROWSER_USE_DISABLE_SECURITY", "false").lower()
                in {"1", "true", "yes", "on"},
                executable_path=chrome_path,
                args=extra_args,
                proxy=proxy_settings,
                allowed_domains=allowed_domains,
                cdp_url=cdp_url,
            )
            await _global_browser.start()

        # Always create a fresh page for each request
        _global_page = await _global_browser.new_page()

        # Create controller and agent
        controller = CustomController()
        _global_agent = CustomAgent(
            task=task,
            add_infos=add_infos,
            use_vision=use_vision,
            llm=llm,
            browser=_global_browser,
            browser_context=_global_page,
            controller=controller,
            max_actions_per_step=max_actions_per_step,
            tool_call_in_content=tool_call_in_content,
            agent_state=_global_agent_state,
        )

        # Run agent
        history = await _global_agent.run(max_steps=max_steps)

        # Extract final result from the agent's history
        final_result = history.final_result()
        if not final_result:
            final_result = f"No final result. Possibly incomplete. {history}"

        return final_result

    except Exception as e:
        logger.error("run-browser-agent error: %s", str(e))
        raise ValueError(f"run-browser-agent error: {e}\n{traceback.format_exc()}")

    finally:
        # Always ensure cleanup, even if no error.
        await _cleanup_browser_resources()


def main() -> None:
    """
    Entry point for running the FastMCP application.
    Handles server start and final resource cleanup.
    """
    try:
        app.run()
    except Exception as e:
        logger.error("Error running MCP server: %s\n%s", e, traceback.format_exc())
    finally:
        # Use a separate event loop to ensure cleanup is awaited properly
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_cleanup_browser_resources())
            loop.close()
        except Exception as cleanup_error:
            logger.error("Cleanup error: %s", cleanup_error)


if __name__ == "__main__":
    main()
