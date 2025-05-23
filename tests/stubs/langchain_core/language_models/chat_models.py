class BaseChatModel:
    async def ainvoke(self, *args, **kwargs):
        return {}
    def with_structured_output(self, *args, **kwargs):
        return self
