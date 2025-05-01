from unittest.mock import MagicMock, patch

import pytest
from news_summarizer.webdriver.creators import (
    ChromeWebDriverCreator,
    EdgeWebDriverCreator,
    FirefoxWebDriverCreator,
)


@pytest.fixture
def mock_webdrivers():
    with patch("news_summarizer.webdriver.creators.webdriver.Chrome") as mock_chrome, \
         patch("news_summarizer.webdriver.creators.webdriver.Edge") as mock_edge, \
         patch("news_summarizer.webdriver.creators.webdriver.Firefox") as mock_firefox:
        yield mock_chrome, mock_edge, mock_firefox


def test_chrome_webdriver_creator(mock_webdrivers):
    mock_chrome, _, _ = mock_webdrivers
    mock_instance = MagicMock()
    mock_chrome.return_value = mock_instance

    creator = ChromeWebDriverCreator()
    driver = creator.create_webdriver()

    mock_chrome.assert_called_once()
    assert driver == mock_instance


def test_edge_webdriver_creator(mock_webdrivers):
    _, mock_edge, _ = mock_webdrivers
    mock_instance = MagicMock()
    mock_edge.return_value = mock_instance

    creator = EdgeWebDriverCreator()
    driver = creator.create_webdriver()

    mock_edge.assert_called_once()
    assert driver == mock_instance


def test_firefox_webdriver_creator(mock_webdrivers):
    _, _, mock_firefox = mock_webdrivers
    mock_instance = MagicMock()
    mock_firefox.return_value = mock_instance

    creator = FirefoxWebDriverCreator()
    driver = creator.create_webdriver()

    mock_firefox.assert_called_once()
    assert driver == mock_instance
