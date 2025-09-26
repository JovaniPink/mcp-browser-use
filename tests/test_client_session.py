import importlib

import pytest

from mcp_browser_use import client as client_module
from mcp_browser_use.client import AgentNotRegisteredError, create_client_session


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio("asyncio")
async def test_create_client_session_uses_supplied_client():
    events = []

    class DummyClient:
        def __init__(self):
            self.connected = False

        async def __aenter__(self):
            events.append("enter")
            self.connected = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            events.append("exit")
            self.connected = False

    dummy = DummyClient()
    async with create_client_session(client=dummy) as session:
        assert session is dummy
        assert dummy.connected

    assert events == ["enter", "exit"]
    assert dummy.connected is False


@pytest.mark.anyio("asyncio")
async def test_create_client_session_accepts_factory():
    events = []

    class DummyClient:
        async def __aenter__(self):
            events.append("enter")
            return self

        async def __aexit__(self, exc_type, exc, tb):
            events.append("exit")

    async with create_client_session(client_factory=DummyClient) as session:
        assert isinstance(session, DummyClient)

    assert events == ["enter", "exit"]


@pytest.mark.anyio("asyncio")
async def test_create_client_session_rejects_mixed_arguments():
    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    dummy = DummyClient()

    with pytest.raises(ValueError):
        async with create_client_session(client=dummy, timeout=5):
            pass

    with pytest.raises(ValueError):
        async with create_client_session(client_factory=DummyClient, timeout=5):
            pass

    with pytest.raises(ValueError):
        async with create_client_session(client=dummy, client_factory=DummyClient):
            pass


@pytest.mark.anyio("asyncio")
async def test_create_client_session_constructs_default_client(monkeypatch):
    created = {}

    class DummyClient:
        def __init__(self, app, **kwargs):
            created["app"] = app
            created["kwargs"] = kwargs

        async def __aenter__(self):
            created["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            created["exited"] = True

    monkeypatch.setattr("mcp_browser_use.client.Client", DummyClient)

    async with create_client_session(timeout=5) as session:
        assert isinstance(session, DummyClient)

    assert created["app"] is client_module.app
    assert created["kwargs"] == {"timeout": 5}
    assert created["entered"] is True
    assert created["exited"] is True


@pytest.mark.anyio("asyncio")
async def test_create_client_session_kwargs_with_factory_raise():
    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    kwargs = {"client_factory": DummyClient, "timeout": 10}

    with pytest.raises(ValueError):
        async with create_client_session(**kwargs):
            pass


def test_legacy_namespace_is_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("mcp_browser.use.mcp_browser_use")


def test_exception_type():
    assert issubclass(AgentNotRegisteredError, RuntimeError)
