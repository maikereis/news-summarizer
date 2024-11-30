from unittest.mock import patch

import pytest
from news_summarizer.webdriver.locators import ShutilBrowserLocator


@pytest.fixture
def browser_locator():
    """Fixture to create a ShutilBrowserLocator instance."""
    return ShutilBrowserLocator()


def test_find_browser_found(browser_locator):
    # Arrange
    browser_name = "google-chrome"
    mock_path = "/usr/bin/google-chrome"

    # Act
    with patch("news_summarizer.webdriver.locators.shutil.which", return_value=mock_path) as mock_which:
        result = browser_locator.find_browser(browser_name)

    # Assert
    mock_which.assert_called_once_with(browser_name)
    assert result == mock_path


def test_find_browser_not_found(browser_locator):
    # Arrange
    browser_name = "nonexistent-browser"

    # Act
    with patch("news_summarizer.webdriver.locators.shutil.which", return_value=None) as mock_which:
        result = browser_locator.find_browser(browser_name)

    # Assert
    mock_which.assert_called_once_with(browser_name)
    assert result is None
