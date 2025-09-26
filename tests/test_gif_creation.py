import sys
import os
import base64
import io

# Add stub package path before importing CustomAgent
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, "stubs"))
sys.path.insert(0, os.path.join(os.path.dirname(BASE_DIR), "src"))

from PIL import Image

from mcp_browser_use.agent.custom_agent import CustomAgent
from browser_use.agent.views import AgentHistoryList, AgentHistory, ActionResult
from browser_use.browser.views import BrowserStateHistory


class DummyState:
    def __init__(self, thought: str):
        self.current_state = type("Brain", (), {"thought": thought})()


def create_screenshot() -> str:
    img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def test_create_history_gif(tmp_path):
    screenshot = create_screenshot()
    hist = AgentHistoryList(
        history=[
            AgentHistory(
                model_output=DummyState("step one"),
                state=BrowserStateHistory(screenshot=screenshot),
                result=[ActionResult(is_done=False)],
            ),
            AgentHistory(
                model_output=DummyState("step two"),
                state=BrowserStateHistory(screenshot=screenshot),
                result=[ActionResult(is_done=True)],
            ),
        ]
    )

    agent = CustomAgent.__new__(CustomAgent)
    agent.history = hist
    agent.task = "My Task"

    output_gif = tmp_path / "out.gif"
    agent.create_history_gif(output_path=str(output_gif))

    assert output_gif.exists()
