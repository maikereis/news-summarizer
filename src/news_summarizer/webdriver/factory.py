from .creators import ChromeWebDriverCreator, EdgeWebDriverCreator, FirefoxWebDriverCreator
from .locators import BrowserLocator


class WebDriverFactory:
    def __init__(self, browser_locator: BrowserLocator):
        self.browser_locator = browser_locator

    def get_webdriver(self):
        firefox_path = self.browser_locator.find_browser("firefox")
        edge_path = self.browser_locator.find_browser("microsoft-edge-stable")
        chrome_path = self.browser_locator.find_browser("google-chrome")

        if chrome_path:
            creator = ChromeWebDriverCreator()
        elif firefox_path:
            creator = FirefoxWebDriverCreator()
        elif edge_path:
            creator = EdgeWebDriverCreator()
        else:
            raise Exception("Neither Chrome nor Edge is installed. Please install one of them.")

        return creator.create_webdriver()
