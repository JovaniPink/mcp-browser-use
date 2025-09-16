import os
import sys

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, "stubs"))
sys.path.insert(0, os.path.join(os.path.dirname(BASE_DIR), "src"))

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

import mcp_browser_use.agent.custom_agent as custom_agent_module


@pytest.fixture
def custom_agent(monkeypatch):
    class DummyMessageManager:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(
        custom_agent_module,
        "CustomMassageManager",
        DummyMessageManager,
    )

    def fake_agent_init(self, *args, **kwargs):
        self.task = kwargs.get("task")
        self.llm = kwargs.get("llm")
        self.browser = kwargs.get("browser")
        self.browser_context = kwargs.get("browser_context")
        self.system_prompt_class = kwargs.get("system_prompt_class")
        self.max_input_tokens = kwargs.get("max_input_tokens")
        self.include_attributes = kwargs.get("include_attributes")
        self.max_error_length = kwargs.get("max_error_length")
        self.max_actions_per_step = kwargs.get("max_actions_per_step")
        self.tool_call_in_content = kwargs.get("tool_call_in_content")
        self.use_vision = kwargs.get("use_vision")
        self.save_conversation_path = kwargs.get("save_conversation_path")
        self.max_failures = kwargs.get("max_failures")
        self.retry_delay = kwargs.get("retry_delay")
        self.validate_output = kwargs.get("validate_output")
        self.n_steps = 0
        self._last_result = None
        self.message_manager = None
        self.history = None
        self.generate_gif = False

    monkeypatch.setattr(custom_agent_module.Agent, "__init__", fake_agent_init)

    return custom_agent_module


def test_custom_agent_creates_independent_default_controllers(custom_agent, monkeypatch):
    controllers = []

    class TrackingController(custom_agent.Controller):
        def __init__(self):
            super().__init__()
            controllers.append(self)

    monkeypatch.setattr(custom_agent, "Controller", TrackingController)

    llm = Mock(spec=BaseChatModel)
    agent_one = custom_agent.CustomAgent(task="Task one", llm=llm)
    agent_two = custom_agent.CustomAgent(task="Task two", llm=llm)

    assert agent_one.controller is not agent_two.controller
    assert controllers == [agent_one.controller, agent_two.controller]


def test_custom_agent_uses_supplied_controller(custom_agent):
    llm = BaseChatModel()
    provided_controller = custom_agent.Controller()

    agent = custom_agent.CustomAgent(
        task="Task with supplied controller",
        llm=llm,
        controller=provided_controller,
    )

    assert agent.controller is provided_controller
