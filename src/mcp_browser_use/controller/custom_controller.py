# -*- coding: utf-8 -*-

import logging
import os
import sys

import pyperclip
from browser_use import BrowserSession
from browser_use.agent.views import ActionResult
from browser_use.controller.service import Controller

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class CustomController(Controller):
    """
    A custom controller registering two clipboard actions: copy and paste.
    """

    def __init__(self):
        super().__init__()
        self._register_custom_actions()

    def _register_custom_actions(self) -> None:
        """Register all custom browser actions for this controller."""

        @self.registry.action("Copy text to clipboard")
        def copy_to_clipboard(text: str) -> ActionResult:
            """
            Copy the given text to the system's clipboard.
            Returns an ActionResult with the same text as extracted_content.
            """
            try:
                pyperclip.copy(text)
                # Be cautious about logging the actual text, if sensitive
                logger.debug("Copied text to clipboard.")
                return ActionResult(extracted_content=text)
            except Exception as e:
                logger.error(f"Error copying text to clipboard: {e}")
                return ActionResult(error=str(e), extracted_content=None)

        @self.registry.action("Paste text from clipboard", requires_browser=True)
        async def paste_from_clipboard(browser_session: BrowserSession) -> ActionResult:
            """
            Paste whatever is currently in the system's clipboard
            into the active browser page by using the send_keys tool.
            """
            try:
                text = pyperclip.paste()
            except Exception as e:
                logger.error(f"Error reading text from clipboard: {e}")
                return ActionResult(error=str(e), extracted_content=None)

            try:
                modifier = "meta" if sys.platform == "darwin" else "ctrl"
                # Use the documented tool via the registry
                await self.registry.execute_action(
                    "send_keys",
                    {"keys": f"{modifier}+v"},
                    browser_session=browser_session,
                )
                logger.debug("Triggered paste shortcut inside the browser session.")
                return ActionResult(extracted_content=text)
            except Exception as e:
                logger.error(f"Error pasting text into the browser session: {e}")
                return ActionResult(error=str(e), extracted_content=None)
