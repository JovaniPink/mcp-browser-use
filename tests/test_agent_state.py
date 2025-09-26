from mcp_browser_use.utils.agent_state import AgentState


def test_agent_state_stop_flow():
    state = AgentState()

    assert state.is_stop_requested() is False

    state.request_stop()
    assert state.is_stop_requested() is True

    state.clear_stop()
    assert state.is_stop_requested() is False


def test_agent_state_last_valid_state_reset():
    state = AgentState()

    marker = {"url": "https://example.com"}
    state.set_last_valid_state(marker)

    assert state.get_last_valid_state() == marker

    state.clear_stop()

    assert state.get_last_valid_state() is None
