import shutil
from abc import ABC, abstractmethod


class BrowserLocator(ABC):
    @abstractmethod
    def find_browser(self, browser_name: str) -> str:
        pass


class ShutilBrowserLocator(BrowserLocator):
    def find_browser(self, browser_name: str) -> str:
        return shutil.which(browser_name)
