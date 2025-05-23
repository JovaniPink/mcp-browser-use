# -*- coding: utf-8 -*-

import asyncio
import logging
import subprocess

import requests
from playwright.async_api import (
    Browser as PlaywrightBrowser,
    BrowserContext as PlaywrightBrowserContext,
    Playwright,
    async_playwright,
)

from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext, BrowserContextConfig

from mcp_browser_use.browser.config import BrowserPersistenceConfig
from mcp_browser_use.browser.custom_context import CustomBrowserContext

logger = logging.getLogger(__name__)


class CustomBrowser(Browser):
    """
    CustomBrowser extends the base Browser to handle multiple scenarios:
      - Connect to a remote browser via WSS URL.
      - Reuse or start a local Chrome instance with remote debugging port (CDP).
      - Launch a headless/non-headless Chromium instance if no path/wss_url is specified.
    """

    async def new_context(
        self, config: BrowserContextConfig = BrowserContextConfig()
    ) -> CustomBrowserContext:
        """
        Create a new CustomBrowserContext using this browser instance.
        """
        return CustomBrowserContext(config=config, browser=self)

    async def _setup_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        """
        Sets up and returns a Playwright Browser instance, handling the following:
          1. If wss_url is configured, connect to that remote browser.
          2. If chrome_instance_path is set, attempt to connect to an existing local
             Chrome instance on port 9222 or launch a new one if it's not running.
          3. Otherwise, launch a new Chromium instance (headless or non-headless).

        :param playwright: The Playwright instance.
        :return: A connected or newly launched PlaywrightBrowser.
        :raises RuntimeError: If unable to connect to or launch a local Chrome instance.
        :raises Exception: If fails to initialize for any other reason.
        """
        # 1) If there's a WebSocket endpoint, connect to remote browser
        if self.config.wss_url:
            logger.info(f"Connecting to remote browser via WSS: {self.config.wss_url}")
            browser = await playwright.chromium.connect(self.config.wss_url)
            return browser

        # 2) If a local Chrome binary path is set, try to connect or launch
        elif self.config.chrome_instance_path:
            return await self._connect_or_launch_local_chrome(playwright)

        # 3) Otherwise, launch a new Chromium instance in headless/non-headless mode
        try:
            # Be careful: this list of arguments can disable security features.
            disable_security_args = []
            if self.config.disable_security:
                disable_security_args = [
                    "--disable-web-security",
                    "--disable-site-isolation-trials",
                    "--disable-features=IsolateOrigins,site-per-process",
                ]

            default_args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-popup-blocking",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-window-activation",
                "--disable-focus-on-load",
                "--no-first-run",
                "--no-default-browser-check",
                "--no-startup-window",
                "--window-position=0,0",
            ]

            logger.debug("Launching Chromium browser with default arguments.")
            browser = await playwright.chromium.launch(
                headless=self.config.headless,
                args=default_args
                + disable_security_args
                + self.config.extra_chromium_args,
                proxy=self.config.proxy,
            )
            logger.info("Successfully launched new Chromium instance.")
            return browser

        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {str(e)}")
            raise

    async def _connect_or_launch_local_chrome(
        self, playwright: Playwright
    ) -> PlaywrightBrowser:
        """
        Attempt to connect to an existing Chrome instance on http://localhost:9222.
        If no instance is found, start a new one from self.config.chrome_instance_path,
        then retry up to 10 times to connect via CDP.
        :param playwright: The active Playwright instance.
        :return: A PlaywrightBrowser object once connected.
        :raises RuntimeError: If we fail to connect or start a new Chrome instance.
        """
        # Attempt connecting to an existing Chrome instance
        try:
            response = requests.get("http://localhost:9222/json/version", timeout=2)
            if response.status_code == 200:
                logger.info("Reusing existing Chrome instance on port 9222.")
                browser = await playwright.chromium.connect_over_cdp(
                    endpoint_url="http://localhost:9222",
                    timeout=20000,
                )
                return browser
        except requests.ConnectionError:
            logger.debug("No existing Chrome instance found on port 9222.")

        # Start a new Chrome instance in the background
        logger.info(
            f"Starting a new Chrome instance from {self.config.chrome_instance_path}..."
        )
        subprocess.Popen(
            [
                self.config.chrome_instance_path,
                "--remote-debugging-port=9222",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Retry connecting for up to 10 seconds (1s intervals)
        for attempt in range(10):
            try:
                response = requests.get("http://localhost:9222/json/version", timeout=2)
                if response.status_code == 200:
                    logger.debug(f"Chrome instance detected on attempt {attempt+1}.")
                    break
            except requests.ConnectionError:
                pass

            logger.debug(f"Waiting for Chrome to start... (attempt {attempt+1}/10)")
            await asyncio.sleep(1)

        # Attempt final connect
        try:
            browser = await playwright.chromium.connect_over_cdp(
                endpoint_url="http://localhost:9222",
                # 20 second timeout
                timeout=20000,
            )
            logger.info("Successfully connected to the new Chrome instance via CDP.")
            return browser
        except Exception as e:
            logger.error(f"Failed to start/connect to new Chrome instance: {str(e)}")
            raise RuntimeError(
                "Could not connect to local Chrome on port 9222. "
                "Close all existing Chrome instances or check your debugging port setup."
            )
