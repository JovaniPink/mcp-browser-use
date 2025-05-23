from dataclasses import dataclass

@dataclass
class BrowserStateHistory:
    url: str = ""
    title: str = ""
    tabs: list = None
    interacted_element: list = None
    screenshot: str | None = None

@dataclass
class BrowserState:
    screenshot: str | None = None
