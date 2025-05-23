class Base:
    pass

class ChatOpenAI:
    root_async_client = None
    model_name = 'mock'
    def with_structured_output(self, *args, **kwargs):
        return self
    async def ainvoke(self, *args, **kwargs):
        return {}
