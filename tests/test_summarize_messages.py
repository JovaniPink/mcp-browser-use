from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import mcp_browser_use.agent.custom_agent as custom_agent_module
from mcp_browser_use.agent.custom_agent import CustomAgent
from browser_use.agent.message_manager.views import MessageHistory, ManagedMessage


class FakeLLM:
    def __init__(self, content: str = "Conversation summary"):
        self.calls = []
        self._content = content

    def invoke(self, input, **kwargs):
        self.calls.append(input)
        message = AIMessage()
        message.content = self._content
        return message

    def __call__(self, input, **kwargs):
        return self.invoke(input, **kwargs)


class DummyMessageManager:
    def __init__(self, extra_messages: int = 6):
        self.system_prompt = SystemMessage()
        self.system_prompt.content = "System instructions"
        self.example_tool_call = AIMessage()
        self.example_tool_call.content = "[]"
        self.example_tool_call.tool_calls = []
        self.reset_calls = 0
        self.history = MessageHistory()
        self.reset_history()
        for idx in range(extra_messages):
            human = HumanMessage()
            human.content = f"User message {idx}"
            self._add_message_with_tokens(human)

    def get_messages(self):
        return [managed.message for managed in self.history.messages]

    def reset_history(self) -> None:
        self.reset_calls += 1
        self.history = MessageHistory()
        self.history.messages = []
        if hasattr(self.history, "total_tokens"):
            self.history.total_tokens = 0
        self._add_message_with_tokens(self.system_prompt)
        self._add_message_with_tokens(self.example_tool_call)

    def _add_message_with_tokens(self, message):
        self.history.messages.append(ManagedMessage(message=message))
        if hasattr(self.history, "total_tokens"):
            self.history.total_tokens += 1


def test_summarize_messages_preserves_system_prompt(monkeypatch):
    class StubChain:
        def __init__(self, llm):
            self.llm = llm

        def invoke(self, data):
            return self.llm.invoke(data)

    class StubPrompt:
        def __or__(self, llm):
            return StubChain(llm)

    class StubChatPromptTemplate:
        @staticmethod
        def from_messages(messages):
            return StubPrompt()

    monkeypatch.setattr(
        custom_agent_module,
        "ChatPromptTemplate",
        StubChatPromptTemplate,
    )

    agent = CustomAgent.__new__(CustomAgent)
    agent.llm = FakeLLM()
    agent.message_manager = DummyMessageManager()

    assert len(agent.message_manager.get_messages()) > 5
    # Ensure the initial reset was performed
    assert agent.message_manager.reset_calls == 1

    result = agent.summarize_messages()

    assert result is True
    assert agent.message_manager.reset_calls == 2

    history_messages = agent.message_manager.history.messages
    assert len(history_messages) == 3
    assert [entry.message for entry in history_messages[:2]] == [
        agent.message_manager.system_prompt,
        agent.message_manager.example_tool_call,
    ]
    assert history_messages[2].message.content == "Conversation summary"
    if hasattr(agent.message_manager.history, "total_tokens"):
        assert agent.message_manager.history.total_tokens == len(history_messages)

    # Ensure the LLM was called with the conversation
    assert len(agent.llm.calls) == 1
    prompt_value = agent.llm.calls[0]
    assert isinstance(prompt_value, dict)
    assert "chat_history" in prompt_value
