from unittest.mock import MagicMock, patch

import pytest
from news_summarizer.webdriver.factory import WebDriverFactory


@pytest.fixture
def mock_browser_locator():
    """Fixture to mock BrowserLocator."""
    with patch("news_summarizer.webdriver.factory.BrowserLocator") as MockBrowserLocator:
        yield MockBrowserLocator.return_value


@pytest.fixture
def mock_chrome_webdriver_creator():
    """Fixture to mock ChromeWebDriverCreator."""
    with patch("news_summarizer.webdriver.factory.ChromeWebDriverCreator") as MockChromeCreator:
        yield MockChromeCreator


@pytest.fixture
def mock_edge_webdriver_creator():
    """Fixture to mock EdgeWebDriverCreator."""
    with patch("news_summarizer.webdriver.factory.EdgeWebDriverCreator") as MockEdgeCreator:
        yield MockEdgeCreator


def test_get_webdriver_chrome(mock_browser_locator, mock_chrome_webdriver_creator):
    # Arrange
    mock_browser_locator.find_browser.side_effect = (
        lambda browser: "/path/to/browser" if browser == "google-chrome" else None
    )
    mock_chrome_instance = MagicMock()
    mock_chrome_webdriver_creator.return_value.create_webdriver.return_value = mock_chrome_instance

    factory = WebDriverFactory(mock_browser_locator)

    # Act
    driver = factory.get_webdriver()

    # Assert
    mock_browser_locator.find_browser.assert_any_call("google-chrome")
    mock_chrome_webdriver_creator.return_value.create_webdriver.assert_called_once()
    assert driver == mock_chrome_instance


def test_get_webdriver_edge(mock_browser_locator, mock_edge_webdriver_creator):
    # Arrange
    mock_browser_locator.find_browser.side_effect = (
        lambda browser: "/path/to/browser" if browser == "microsoft-edge-stable" else None
    )
    mock_edge_instance = MagicMock()
    mock_edge_webdriver_creator.return_value.create_webdriver.return_value = mock_edge_instance

    factory = WebDriverFactory(mock_browser_locator)

    # Act
    driver = factory.get_webdriver()

    # Assert
    mock_browser_locator.find_browser.assert_any_call("microsoft-edge-stable")
    mock_edge_webdriver_creator.return_value.create_webdriver.assert_called_once()
    assert driver == mock_edge_instance


def test_get_webdriver_no_browser(mock_browser_locator):
    # Arrange
    mock_browser_locator.find_browser.return_value = None
    factory = WebDriverFactory(mock_browser_locator)

    # Act & Assert
    with pytest.raises(Exception, match="Neither Chrome nor Edge is installed. Please install one of them."):
        factory.get_webdriver()
