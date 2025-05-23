class BaseChatModel:
    def with_structured_output(self, *args, **kwargs):
        return self
    async def ainvoke(self, *args, **kwargs):
        return {}
