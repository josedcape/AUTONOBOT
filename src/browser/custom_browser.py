import asyncio
import os
import logging
import socket

from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import (
    BrowserContext as PlaywrightBrowserContext,
)
from playwright.async_api import (
    Playwright,
    async_playwright,
)

# Import from browser_use
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

from .custom_context import CustomBrowserContext

# Define constants that were previously imported
IN_DOCKER = os.environ.get('IN_DOCKER', False)

# Chrome arguments - define locally since they're not available in the new version
CHROME_ARGS = [
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection',
]

CHROME_HEADLESS_ARGS = ['--headless=new']
CHROME_DISABLE_SECURITY_ARGS = [
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor',
]
CHROME_DETERMINISTIC_RENDERING_ARGS = [
    '--run-all-compositor-stages-before-draw',
    '--disable-new-content-rendering-timeout',
]
CHROME_DOCKER_ARGS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
]

logger = logging.getLogger(__name__)

# Simple utility functions to replace missing imports
def get_screen_resolution():
    """Get screen resolution - simplified version"""
    return {'width': 1920, 'height': 1080}

def get_window_adjustments():
    """Get window adjustments - simplified version"""
    return 0, 0


class CustomBrowser(Browser):

    async def new_context(self, config: BrowserContextConfig | None = None) -> CustomBrowserContext:
        """Create a browser context"""
        # Use the provided config or create a default one
        if config is None:
            config = BrowserContextConfig()
        return CustomBrowserContext(config=config, browser=self)

    async def _setup_builtin_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        """Sets up and returns a Playwright Browser instance with anti-detection measures."""
        # Simplified version that works with current browser_use

        # Default screen size
        screen_size = {'width': 1920, 'height': 1080}
        offset_x, offset_y = 0, 0

        # Basic chrome arguments
        chrome_args = [
            '--remote-debugging-port=9222',
            *CHROME_ARGS,
            *(CHROME_DOCKER_ARGS if IN_DOCKER else []),
            *(CHROME_HEADLESS_ARGS if getattr(self.config, 'headless', False) else []),
            *(CHROME_DISABLE_SECURITY_ARGS if getattr(self.config, 'disable_security', False) else []),
            f'--window-position={offset_x},{offset_y}',
            f'--window-size={screen_size["width"]},{screen_size["height"]}',
        ]

        # Get browser class - default to chromium
        browser_class = getattr(playwright, 'chromium')

        browser = await browser_class.launch(
            headless=getattr(self.config, 'headless', False),
            args=chrome_args,
            handle_sigterm=False,
            handle_sigint=False,
        )
        return browser
