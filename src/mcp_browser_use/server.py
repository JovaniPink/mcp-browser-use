"""FastMCP server entry point backed by browser-use's public API."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from browser_use import Agent, BrowserSession
from fastmcp import FastMCP

from mcp_browser_use.browser.browser_manager import create_browser_session
from mcp_browser_use.utils.llm import get_llm_model
from mcp_browser_use.utils.logging import configure_logging

configure_logging()

logger = logging.getLogger(__name__)

app = FastMCP("mcp_browser_use")

_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    try:
        value = int(raw_value) if raw_value is not None else default
    except ValueError:
        logger.warning("Invalid integer for %s; using %s", name, default)
        value = default
    return max(minimum, min(maximum, value))


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    try:
        return float(raw_value) if raw_value is not None else default
    except ValueError:
        logger.warning("Invalid float for %s; using %s", name, default)
        return default


@dataclass(frozen=True, slots=True)
class AgentRuntimeConfig:
    """Validated environment-backed settings for one browser agent run."""

    provider: str
    model: str
    temperature: float
    max_steps: int
    max_actions_per_step: int
    use_vision: bool

    @classmethod
    def from_env(cls) -> AgentRuntimeConfig:
        return cls(
            provider=os.getenv("MCP_MODEL_PROVIDER", "anthropic").strip().lower(),
            model=os.getenv("MCP_MODEL_NAME", "claude-sonnet-4-6").strip(),
            temperature=_env_float("MCP_TEMPERATURE", 0.3),
            max_steps=_env_int("MCP_MAX_STEPS", 30, minimum=1, maximum=100),
            max_actions_per_step=_env_int(
                "MCP_MAX_ACTIONS_PER_STEP", 5, minimum=1, maximum=20
            ),
            use_vision=os.getenv("MCP_USE_VISION", "true").lower() in _TRUE_VALUES,
        )


def _task_with_context(task: str, add_infos: str) -> str:
    task = task.strip()
    if not task:
        raise ValueError("task must not be empty")
    if not add_infos.strip():
        return task
    return f"{task}\n\nAdditional context:\n{add_infos.strip()}"


async def execute_browser_agent(task: str, add_infos: str = "") -> str:
    """Execute one isolated browser-use agent and always release its session."""

    runtime = AgentRuntimeConfig.from_env()
    browser_session: BrowserSession | None = None

    try:
        llm = get_llm_model(
            runtime.provider,
            model_name=runtime.model,
            temperature=runtime.temperature,
        )
        browser_session = create_browser_session()
        agent = Agent(
            task=_task_with_context(task, add_infos),
            llm=llm,
            browser_session=browser_session,
            use_vision=runtime.use_vision,
            max_actions_per_step=runtime.max_actions_per_step,
            source="mcp-browser-use",
        )
        history = await agent.run(max_steps=runtime.max_steps)
        return history.final_result() or "Agent stopped without a final result."
    except Exception as error:
        logger.exception("Browser agent run failed")
        raise RuntimeError("Browser agent run failed; inspect server logs.") from error
    finally:
        if browser_session is not None:
            try:
                await browser_session.stop()
            except Exception:
                logger.warning("Graceful browser stop failed; forcing shutdown")
                try:
                    await browser_session.kill()
                except Exception:
                    logger.exception("Forced browser shutdown also failed")


@app.tool()
async def run_browser_agent(task: str, add_infos: str = "") -> str:
    """Run a browser automation task with optional additional context."""

    return await execute_browser_agent(task, add_infos)


def launch_mcp_browser_use_server() -> None:
    """Launch the MCP server using FastMCP's default stdio transport."""

    app.run()


if __name__ == "__main__":
    launch_mcp_browser_use_server()
