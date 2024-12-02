from abc import ABC, abstractmethod
from tempfile import mkdtemp

import chromedriver_autoinstaller
import edgedriver_autoinstaller
from selenium import webdriver


class WebDriverCreator(ABC):
    @abstractmethod
    def create_webdriver(self):
        pass


class ChromeWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        # print("Chrome is installed. Installing and using chromedriver...")
        chromedriver_autoinstaller.install()
        options = webdriver.ChromeOptions()
        self._set_common_options(options)
        return webdriver.Chrome(options=options)

    def _set_common_options(self, options):
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--profile.default_content_settings.cookies=2")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9226")


class EdgeWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        # print("Edge is installed. Installing and using edgedriver...")
        edgedriver_autoinstaller.install()
        options = webdriver.EdgeOptions()
        self._set_common_options(options)
        return webdriver.Edge(options=options)

    def _set_common_options(self, options):
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--profile.default_content_settings.cookies=2")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9226")
