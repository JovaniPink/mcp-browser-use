class _Registry:
    def get_prompt_description(self):
        return ""

    def create_action_model(self):
        return type("ActionModel", (), {})

    def action(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


class Controller:
    def __init__(self):
        self.registry = _Registry()

    async def multi_act(self, actions, context):  # pragma: no cover - stub
        return []
