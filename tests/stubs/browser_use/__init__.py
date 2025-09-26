class _DummyEvent:
    def __await__(self):
        async def _noop():
            return None

        return _noop().__await__()

    async def event_result(self, *args, **kwargs):  # pragma: no cover - stub method
        return None


class _DummyEventBus:
    def dispatch(self, event):  # noqa: D401 - simple stub
        return _DummyEvent()


class BrowserPage:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.event_bus = _DummyEventBus()

    async def close(self) -> None:  # pragma: no cover - stub method
        return None


class Browser:
    """Lightweight stub mirroring the public Browser API used in tests."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._pages: list[BrowserPage] = []
        self._started = False

    async def start(self):  # pragma: no cover - stub method
        self._started = True
        return self

    async def stop(self):  # pragma: no cover - stub method
        self._started = False
        return None

    async def new_page(self, **kwargs):
        page = BrowserPage(**kwargs)
        self._pages.append(page)
        return page

    async def close(self):  # pragma: no cover - compatibility alias
        return await self.stop()


class BrowserProfile:  # pragma: no cover - stub class
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
