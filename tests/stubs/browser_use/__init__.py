class _DummyEvent:
    def __await__(self):
        async def _noop():
            return None

        return _noop().__await__()

    async def event_result(self, *args, **kwargs):
        return None


class _DummyEventBus:
    def dispatch(self, event):  # noqa: D401 - simple stub
        return _DummyEvent()


class BrowserSession:
    """Lightweight stub mirroring the public BrowserSession API used in tests."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.event_bus = _DummyEventBus()

    async def kill(self) -> None:  # pragma: no cover - stub method
        return None


class BrowserProfile:  # pragma: no cover - stub class
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class ProxySettings:  # pragma: no cover - stub class
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Alias maintained for compatibility with production package
Browser = BrowserSession


__all__ = ["Browser", "BrowserSession", "BrowserProfile", "ProxySettings"]
