class Controller:
    def __init__(self):
        self.registry = type('Registry', (), {
            'get_prompt_description': lambda self: '',
            'create_action_model': lambda self: type('ActionModel', (), {})
        })()
    async def multi_act(self, actions, context):
        return []
