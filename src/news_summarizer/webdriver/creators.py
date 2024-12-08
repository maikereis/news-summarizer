from abc import ABC, abstractmethod
from tempfile import mkdtemp

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

chrome_driver_path = ChromeDriverManager().install()
edge_driver_path = EdgeChromiumDriverManager().install()


class WebDriverCreator(ABC):
    @abstractmethod
    def create_webdriver(self):
        pass


class ChromeWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        service = Service(chrome_driver_path)
        options = webdriver.ChromeOptions()
        self._set_common_options(options)
        return webdriver.Chrome(service=service, options=options)

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
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        # options.add_argument("--remote-debugging-port=9222") ## BUG HERE


class EdgeWebDriverCreator(WebDriverCreator):
    def create_webdriver(self):
        service = Service(edge_driver_path)
        options = webdriver.EdgeOptions()
        self._set_common_options(options)
        return webdriver.Edge(service=service, options=options)

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
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        # options.add_argument("--remote-debugging-port=9222") ## BUG HERE
