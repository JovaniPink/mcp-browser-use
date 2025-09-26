# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import traceback
import logging
from typing import Any, Optional

from browser_use import Browser
from fastmcp import FastMCP
from mcp_browser_use.agent.custom_agent import CustomAgent
from mcp_browser_use.controller.custom_controller import CustomController
from mcp_browser_use.browser.browser_manager import create_browser_session
from mcp_browser_use.utils import utils
from mcp_browser_use.utils.agent_state import AgentState

# Configure logging for the entire module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP("mcp_browser_use")


@app.tool()
async def run_browser_agent(task: str, add_infos: str = "") -> str:
    """
    This is the entrypoint for running a browser-based agent.

    :param task: The main instruction or goal for the agent.
    :param add_infos: Additional information or context for the agent.
    :return: The final result string from the agent run.
    """

    browser_session: Optional[Browser] = None
    agent_state = AgentState()

    try:
        # Clear any previous agent stop signals
        agent_state.clear_stop()

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

        # Create a fresh browser session for this run
        browser_session = create_browser_session()
        if hasattr(browser_session, "start"):
            await browser_session.start()

        # Create controller and agent
        controller = CustomController()
        agent = CustomAgent(
            task=task,
            add_infos=add_infos,
            use_vision=use_vision,
            llm=llm,
            browser_session=browser_session,
            controller=controller,
            max_actions_per_step=max_actions_per_step,
            tool_call_in_content=tool_call_in_content,
            agent_state=agent_state,
        )

        # Execute the agent task lifecycle
        history = await agent.execute_agent_task(max_steps=max_steps)

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
        try:
            agent_state.request_stop()
        except Exception as stop_error:
            logger.warning("Error stopping agent state: %s", stop_error)

        if browser_session:
            try:
                await browser_session.stop()
            except Exception as browser_error:
                logger.warning(
                    "Failed to stop browser session gracefully, killing it: %s",
                    browser_error,
                )
                if hasattr(browser_session, "kill"):
                    await browser_session.kill()


def launch_mcp_browser_use_server() -> None:
    """
    Entry point for running the FastMCP application.
    Handles server start and final resource cleanup.
    """
    try:
        app.run()
    except Exception as e:
        logger.error("Error running MCP server: %s\n%s", e, traceback.format_exc())


if __name__ == "__main__":
    launch_mcp_browser_use_server()
