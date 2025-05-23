class Agent:
    def __init__(self, *args, **kwargs):
        self.history = kwargs.get('history', None)
        self.generate_gif = False
