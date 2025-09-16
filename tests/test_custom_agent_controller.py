import os
import sys

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, "stubs"))
sys.path.insert(0, os.path.join(os.path.dirname(BASE_DIR), "src"))

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from unittest.mock import Mock

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
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Set attributes not passed in kwargs that are needed
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
    llm = Mock(spec=BaseChatModel)
    provided_controller = custom_agent.Controller()

    agent = custom_agent.CustomAgent(
        task="Task with supplied controller",
        llm=llm,
        controller=provided_controller,
    )

    assert agent.controller is provided_controller
