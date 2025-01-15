from abc import ABC, abstractmethod

from news_summarizer.domain.base import NoSQLBaseDocument
from news_summarizer.webdriver import ShutilBrowserLocator, WebDriverFactory


class BaseCrawler(ABC):
    model: type[NoSQLBaseDocument]

    @abstractmethod
    def search(self, link: str, **kwargs) -> None:
        raise NotImplementedError


class BaseSeleniumCrawler(BaseCrawler, ABC):
    def __init__(self, scroll_limit: int = 5) -> None:
        self.driver = WebDriverFactory(ShutilBrowserLocator()).get_webdriver()
        self.scroll_limit = scroll_limit
        self.soup = None
