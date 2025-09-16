class Base:
    pass

class ChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass

    root_async_client = None
    model_name = 'mock'
    def with_structured_output(self, *args, **kwargs):
        return self
    async def ainvoke(self, *args, **kwargs):
        return {}


class AzureChatOpenAI(ChatOpenAI):
    """Minimal stub mirroring the OpenAI chat client API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

