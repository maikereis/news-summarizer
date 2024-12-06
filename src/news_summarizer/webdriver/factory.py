from .creators import ChromeWebDriverCreator, EdgeWebDriverCreator
from .locators import BrowserLocator


class WebDriverFactory:
    def __init__(self, browser_locator: BrowserLocator):
        self.browser_locator = browser_locator

    def get_webdriver(self):
        chrome_path = self.browser_locator.find_browser("google-chrome")
        edge_path = self.browser_locator.find_browser("microsoft-edge-stable")

        if edge_path:
            creator = EdgeWebDriverCreator()
        elif chrome_path:
            creator = ChromeWebDriverCreator()
        else:
            raise Exception("Neither Chrome nor Edge is installed. Please install one of them.")

        return creator.create_webdriver()
