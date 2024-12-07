from abc import ABC, abstractmethod

from news_summarizer.domain.base import NoSQLBaseLink
from news_summarizer.webdriver import ShutilBrowserLocator, WebDriverFactory


class BaseScraper(ABC):
    model: type[NoSQLBaseLink]

    @abstractmethod
    def extract(self, link: str, **kwargs) -> None:
        raise NotImplementedError


class BaseSeleniumScraper(BaseScraper, ABC):
    def __init__(self, scroll_limit: int = 5) -> None:
        self.driver = WebDriverFactory(ShutilBrowserLocator()).get_webdriver()
        self.scroll_limit = scroll_limit
        self.soup = None
