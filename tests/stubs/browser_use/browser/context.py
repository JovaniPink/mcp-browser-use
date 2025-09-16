class BrowserContextConfig:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class BrowserContext:
    async def get_state(self, *args, **kwargs):
        pass

    async def close(self):
        pass
