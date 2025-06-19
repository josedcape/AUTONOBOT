import logging

from browser_use import Browser
from browser_use.browser.context import BrowserContext, BrowserContextConfig

logger = logging.getLogger(__name__)


class CustomBrowserContext(BrowserContext):
    def __init__(
            self,
            browser: 'Browser',
            config: BrowserContextConfig | None = None,
    ):
        if config is None:
            config = BrowserContextConfig()
        super(CustomBrowserContext, self).__init__(browser=browser, config=config)
