"""FastMCP server entry point backed by browser-use's public API."""

from __future__ import annotations

import asyncio
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
_MAX_TASK_CHARS = 20_000
_MAX_CONTEXT_CHARS = 20_000


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    try:
        value = int(raw_value) if raw_value is not None else default
    except ValueError:
        logger.warning("Invalid integer for %s; using %s", name, default)
        value = default
    return max(minimum, min(maximum, value))


def _env_optional_float(name: str, *, minimum: float, maximum: float) -> float | None:
    """Return a clamped float, or ``None`` so the provider keeps its default."""

    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return None
    try:
        value = float(raw_value)
    except ValueError:
        logger.warning("Invalid float for %s; using the provider default", name)
        return None
    return max(minimum, min(maximum, value))


@dataclass(frozen=True, slots=True)
class AgentRuntimeConfig:
    """Validated environment-backed settings for one browser agent run."""

    provider: str
    model: str
    temperature: float | None
    max_steps: int
    max_actions_per_step: int
    use_vision: bool
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> AgentRuntimeConfig:
        return cls(
            provider=os.getenv("MCP_MODEL_PROVIDER", "anthropic").strip().lower(),
            model=os.getenv("MCP_MODEL_NAME", "claude-opus-5").strip(),
            # Unset by default: current Anthropic models reject sampling params.
            temperature=_env_optional_float(
                "MCP_TEMPERATURE", minimum=0.0, maximum=2.0
            ),
            max_steps=_env_int("MCP_MAX_STEPS", 30, minimum=1, maximum=100),
            max_actions_per_step=_env_int(
                "MCP_MAX_ACTIONS_PER_STEP", 5, minimum=1, maximum=20
            ),
            use_vision=os.getenv("MCP_USE_VISION", "true").lower() in _TRUE_VALUES,
            timeout_seconds=_env_int(
                "MCP_RUN_TIMEOUT_SECONDS", 600, minimum=30, maximum=3600
            ),
        )


# Each run owns a Chromium process; bound how many exist at once. Read once at
# import because the semaphore must be shared by every request in the process.
_MAX_CONCURRENT_RUNS = _env_int("MCP_MAX_CONCURRENT_RUNS", 1, minimum=1, maximum=8)
_run_slots = asyncio.Semaphore(_MAX_CONCURRENT_RUNS)


def _task_with_context(task: str, add_infos: str) -> str:
    task = task.strip()
    if not task:
        raise ValueError("task must not be empty")
    if len(task) > _MAX_TASK_CHARS:
        raise ValueError(f"task must not exceed {_MAX_TASK_CHARS} characters")

    add_infos = add_infos.strip()
    if len(add_infos) > _MAX_CONTEXT_CHARS:
        raise ValueError(f"add_infos must not exceed {_MAX_CONTEXT_CHARS} characters")
    if not add_infos:
        return task
    return f"{task}\n\nAdditional context:\n{add_infos}"


async def execute_browser_agent(task: str, add_infos: str = "") -> str:
    """Execute one isolated browser-use agent and always release its session."""

    task_prompt = _task_with_context(task, add_infos)
    runtime = AgentRuntimeConfig.from_env()
    async with _run_slots:
        return await _run_agent(task_prompt, runtime)


async def _run_agent(task_prompt: str, runtime: AgentRuntimeConfig) -> str:
    browser_session: BrowserSession | None = None
    deadline: asyncio.Timeout | None = None

    try:
        llm = get_llm_model(
            runtime.provider,
            model_name=runtime.model,
            temperature=runtime.temperature,
        )
        browser_session = create_browser_session()
        agent = Agent(
            task=task_prompt,
            llm=llm,
            browser_session=browser_session,
            use_vision=runtime.use_vision,
            max_actions_per_step=runtime.max_actions_per_step,
            source="mcp-browser-use",
        )
        deadline = asyncio.timeout(runtime.timeout_seconds)
        async with deadline:
            history = await agent.run(max_steps=runtime.max_steps)
        return history.final_result() or "Agent stopped without a final result."
    except TimeoutError as error:
        # Only the run deadline is reported as a timeout; a TimeoutError raised
        # inside the agent (e.g. a network call) is an ordinary failure.
        if deadline is None or not deadline.expired():
            logger.exception("Browser agent run failed")
            raise RuntimeError(
                "Browser agent run failed; inspect server logs."
            ) from error
        logger.warning("Browser agent run exceeded %ss", runtime.timeout_seconds)
        raise RuntimeError(
            f"Browser agent run timed out after {runtime.timeout_seconds} seconds."
        ) from error
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
