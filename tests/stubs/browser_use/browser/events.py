class SendKeysEvent:
    def __init__(self, keys: str):
        self.keys = keys


class ScreenshotEvent:
    def __init__(self, full_page: bool = False):
        self.full_page = full_page
