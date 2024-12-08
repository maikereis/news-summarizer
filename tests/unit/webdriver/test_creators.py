from unittest.mock import MagicMock, patch

import pytest
from news_summarizer.webdriver.creators import ChromeWebDriverCreator, EdgeWebDriverCreator


@pytest.fixture
def mock_chromedriver_manager():
    with patch("news_summarizer.webdriver.creators.ChromeDriverManager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_edgedriver_manager():
    with patch("news_summarizer.webdriver.creators.EdgeChromiumDriverManager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_webdriver():
    with (
        patch("news_summarizer.webdriver.creators.webdriver.Chrome") as mock_chrome,
        patch("news_summarizer.webdriver.creators.webdriver.Edge") as mock_edge,
    ):
        yield mock_chrome, mock_edge


def test_chrome_webdriver_creator(mock_chromedriver_manager, mock_webdriver):
    mock_chrome, _ = mock_webdriver
    mock_chrome_instance = MagicMock()
    mock_chrome.return_value = mock_chrome_instance

    creator = ChromeWebDriverCreator()
    driver = creator.create_webdriver()

    assert driver == mock_chrome_instance  # Ensure the driver returned is correct


def test_edge_webdriver_creator(mock_edgedriver_manager, mock_webdriver):
    _, mock_edge = mock_webdriver
    mock_edge_instance = MagicMock()
    mock_edge.return_value = mock_edge_instance

    creator = EdgeWebDriverCreator()
    driver = creator.create_webdriver()

    mock_edge.assert_called_once()  # Ensure Edge driver is called
    assert driver == mock_edge_instance  # Ensure the driver returned is correct
