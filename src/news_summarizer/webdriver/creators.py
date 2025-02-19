from abc import ABC, abstractmethod

from selenium import webdriver


class WebDriverCreator(ABC):
    @abstractmethod
    def create_webdriver(self):
        pass


class ChromeWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        # Selenium Manager automatically handles driver management
        options = webdriver.ChromeOptions()
        self._set_common_options(options)
        return webdriver.Chrome(options=options)

    def _set_common_options(self, options):
        options.add_argument("--no-sandbox")
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-networking")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--profile.default_content_settings.cookies=2")


class EdgeWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        # Selenium Manager automatically handles driver management
        options = webdriver.EdgeOptions()
        self._set_common_options(options)
        return webdriver.Edge(options=options)

    def _set_common_options(self, options):
        options.add_argument("--no-sandbox")
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-networking")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--profile.default_content_settings.cookies=2")


class FirefoxWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        # Selenium Manager automatically handles driver management
        options = webdriver.FirefoxOptions()
        self._set_common_options(options)
        return webdriver.Firefox(options=options)

    def _set_common_options(self, options):
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")  # Avoid /dev/shm usage
        options.add_argument("--log-level=3")  # Suppress logging
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-networking")
        options.add_argument("--ignore-certificate-errors")
        options.set_preference("permissions.default.image", 2)
