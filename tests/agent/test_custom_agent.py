import pytest
from mcp_browser_use.agent.custom_agent import CustomAgent
from mcp_browser_use.utils.agent_state import AgentState
from langchain_core.language_models.chat_models import BaseChatModel


class FakeLLM(BaseChatModel):
    # Minimal fake LLM to simulate structured responses
    async def ainvoke(self, messages):
        # Return a structured "AgentOutput" style response
        return {
            "content": '{"current_state": {"prev_action_evaluation":"Success","important_contents":"","completed_contents":"","thought":"","summary":""}, "action":[]}'
        }


@pytest.mark.asyncio
async def test_agent_run_single_step():
    llm = FakeLLM()
    agent_state = AgentState()
    agent = CustomAgent(task="Test Task", llm=llm, agent_state=agent_state)
    output = await agent.run(max_steps=1)
    assert output is not None
    # Check if final_result is set
    assert "No final result" not in output.final_result()
    # No concurrency or browser checks here—just ensure the agent doesn't crash
