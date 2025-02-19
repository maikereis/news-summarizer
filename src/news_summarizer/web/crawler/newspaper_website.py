import logging
import re
import time
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from news_summarizer.domain.documents import Link
from news_summarizer.utils import clean_html

from .base import BaseSeleniumCrawler

logging.basicConfig(level=logging.debug)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
MAX_REPEATED_PAGE_COUNT = 10
TIMEOUT = 300


def extract_date_from_url(url: str) -> str:
    # Regular expression to match the date in the format YYYY/MM/DD

    try:
        pattern0 = r"(\d{4}/\d{2}/\d{2})"
        pattern1 = r"(\d{2}\d{2}\d{4})"

        match = re.search(pattern0, url)

        if match:
            date_str = match.group(0)
            # Convert the date string to a datetime object
            return datetime.strptime(date_str, "%Y/%m/%d")

        match = re.search(pattern1, url)

        if match:
            date_str = match.group(0)
            # Convert the date string to a datetime object
            return datetime.strptime(date_str, "%d%m%Y")
    except Exception:
        logger.error("Error trying to parse date for %s", url)
    return None


def extract_title(url: str) -> str:
    last_segment = url.rsplit("/", 1)[-1]

    # Remove HTML-like extensions
    last_segment = re.sub(r"\.html?|\.htm|\.ghtml$", "", last_segment)

    # Replace separators (-, _, etc.) with spaces and convert to lowercase
    title = re.sub(r"[-_]", " ", last_segment)

    # Optional: Replace multiple spaces with a single space
    title = re.sub(r"\s+", " ", title).strip()

    return title


def extract_links(elements: List[Tag]):
    data = []
    for element in elements:
        url = element.get("href")

        title = element.get_text(strip=True)
        if len(title) < 5:
            title = extract_title(url)

        published_at = extract_date_from_url(url)

        link = {
            "title": title,
            "url": url,
            "published_at": published_at,
        }

        data.append(link)

    return data


class G1Crawler(BaseSeleniumCrawler):
    model = Link

    def __init__(self, scroll_limit: int = 50) -> None:
        super().__init__(scroll_limit=scroll_limit)

    def scroll_page(self) -> None:
        logger.debug("Start scrolling page.")

        load_more = 0
        page_number = 0
        last_page_number = 0
        repeated_page_count = 0
        retry_count = 0

        timeout_duration = TIMEOUT  # 10 minutes # Record the start time start_time = time.time()
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                logger.debug("Timeout reached. Stopping the crawl.")
                break

            if retry_count > MAX_RETRIES:
                logger.debug("Max retries reached.")
                break

            try:
                logger.debug("Scrolling page down.")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script(
                        "return window.pageYOffset + window.innerHeight >= document.body.scrollHeight"
                    )
                )

                logger.debug("Waiting for the button to be clickable.")

                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.load-more a"))
                )

                url = load_more_button.get_dom_attribute("href")

                page_number = self._extract_page_number(url)

                if not isinstance(
                    page_number,
                    int,
                ):
                    logger.debug("Invalid page number.")
                    continue

                logger.debug("Current page number: %s", page_number)

                ## Break if the page is not being updated
                if page_number == last_page_number:
                    repeated_page_count += 1
                    logger.warning("Seeing the same page for %s interactions.", repeated_page_count)
                else:
                    repeated_page_count = 0

                if repeated_page_count > MAX_REPEATED_PAGE_COUNT:
                    logger.debug("Skipping, seeing the same page for %s iteractions.", repeated_page_count)
                    break

                ## Break if the maximum number of scrolls is reached.
                if page_number > last_page_number:
                    logger.debug("New content loaded.")
                    load_more += 1
                    last_page_number = page_number
                    if load_more >= self.scroll_limit:
                        logger.debug("Reached scrolls limit: %s", load_more)
                        break

                logger.debug("Loading more content.")
                self.driver.execute_script("arguments[0].click()", load_more_button)
                time.sleep(1)

            except TimeoutException:
                retry_count += 1
                logger.warning("Timeout.")
                continue
            except Exception as ex:
                logger.error("Unexpected error in scroll_page: %s", ex)
                break

    def _extract_page_number(self, url):
        match = re.search(r"pagina-(\d+)", url)
        page_number = int(match.group(1))

        if isinstance(page_number, int):
            return page_number
        return None

    def accept_cookies(self):
        button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cookie-banner-lgpd_accept-button"))
        )

        self.driver.execute_script("arguments[0].click()", button)

    def search(self, link: str, **kwargs) -> None:
        try:
            logger.debug("Crawling link: %s", link)
            self.driver.get(link)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "footer")))
            time.sleep(2)
            self.accept_cookies()
            time.sleep(2)
            self.scroll_page()

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            soup = clean_html(soup)
            elements = soup.find_all("a", href=True)
            hyperlinks = extract_links(elements)
            self.driver.close()

            hyperlink_list = []
            for hyperlink in hyperlinks:
                try:
                    hyperlink_list.append(
                        Link(
                            title=hyperlink["title"],
                            url=hyperlink["url"],
                            source=link,
                            published_at=hyperlink["published_at"],
                        )
                    )
                except ValueError:
                    logger.error(
                        "Failed to append hyperlink with title '%s' and URL '%s'",
                        hyperlink.get("title", "N/A"),
                        hyperlink.get("url", "N/A"),
                    )
                    continue

            logger.debug("Found %s hyperlinks on '%s'", len(hyperlink_list), link)
            self.model.bulk_insert(hyperlink_list)
        except Exception as ex:
            logger.error("Error while crawling domain %s: %s", link, ex)
            raise
        finally:
            self.driver.close()


class BandCrawler(BaseSeleniumCrawler):
    model = Link

    def __init__(self, scroll_limit: int = 50) -> None:
        super().__init__(scroll_limit=scroll_limit)

    def scroll_page(self) -> None:
        logger.debug("Start scrolling page.")

        load_more = 0
        page_number = 0
        last_page_number = 0
        repeated_page_count = 0
        retry_count = 0

        timeout_duration = TIMEOUT  # 10 minutes # Record the start time start_time = time.time()
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                logger.debug("Timeout reached. Stopping the crawl.")
                break

            if retry_count > MAX_RETRIES:
                logger.debug("Max retries reached.")
                break

            try:
                logger.debug("Scrolling page down.")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script(
                        "return window.pageYOffset + window.innerHeight >= document.body.scrollHeight"
                    )
                )

                logger.debug("Waiting for the button to be clickable.")

                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cs-load-more"))
                )

                page_number = int(load_more_button.get_attribute("data-page"))

                if not isinstance(
                    page_number,
                    int,
                ):
                    logger.debug("Invalid page number.")
                    continue

                logger.debug("Current page number: %s", page_number)

                if page_number == last_page_number:
                    repeated_page_count += 1
                    logger.debug("Seeing the same page for %s interactions", repeated_page_count)
                else:
                    repeated_page_count = 0

                if repeated_page_count > MAX_REPEATED_PAGE_COUNT:
                    logger.debug("Skipping, seeing the same page for %s iteractions.", repeated_page_count)
                    break

                ## Break if the maximum number of scrolls is reached.
                if page_number > last_page_number:
                    logger.debug("New content loaded.")
                    load_more += 1
                    last_page_number = page_number
                    if load_more >= self.scroll_limit:
                        logger.debug("Reached scrolls limit: %s", load_more)
                        break

                logger.debug("Loading more content.")
                self.driver.execute_script("arguments[0].click()", load_more_button)
                time.sleep(2)

            except TimeoutException:
                retry_count += 1
                logger.warning("Timeout.")
                continue
            except StaleElementReferenceException as exc:
                retry_count += 1
                logger.warning("Stale element found during scroll: %s", exc)
                continue
            except Exception as ex:
                logger.error("Unexpected error in scroll_page: %s", ex)
                break

    def search(self, link: str, **kwargs) -> None:
        try:
            logger.debug("Crawling link: %s", link)
            self.driver.get(link)
            time.sleep(5)
            self.scroll_page()
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            soup = clean_html(soup)
            elements = soup.find_all("a", href=True)
            hyperlinks = extract_links(elements)

            if len(hyperlinks) == 0:
                logger.error("No links found.")

            self.driver.close()

            hyperlink_list = []
            for hyperlink in hyperlinks:
                try:
                    hyperlink_list.append(
                        Link(
                            title=hyperlink["title"],
                            url=hyperlink["url"],
                            source=link,
                            published_at=hyperlink["published_at"],
                        )
                    )
                except ValueError:
                    logger.error(
                        "Failed to append hyperlink with title '%s' and URL '%s'",
                        hyperlink.get("title", "N/A"),
                        hyperlink.get("url", "N/A"),
                    )
                    continue

            logger.debug("Found %s hyperlinks on '%s'", len(hyperlink_list), link)
            self.model.bulk_insert(hyperlink_list)
        except Exception as ex:
            logger.error("Error while crawling domain %s: %s", link, ex)
            raise
        finally:
            self.driver.close()


class R7Crawler(BaseSeleniumCrawler):
    model = Link

    def __init__(self, scroll_limit: int = 50) -> None:
        super().__init__(scroll_limit=scroll_limit)

    def scroll_page(self) -> None:
        logger.debug("Start scrolling page.")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        load_more = 0
        retry_count = 0
        timeout_duration = TIMEOUT  # 10 minutes # Record the start time start_time = time.time()
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                logger.debug("Timeout reached. Stopping the crawl.")

            if retry_count > MAX_RETRIES:
                logger.debug("Max retries reached.")
                break

            try:
                logger.debug("Scrolling page down.")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script(
                        "return window.pageYOffset + window.innerHeight >= document.body.scrollHeight"
                    )
                )

                logger.debug("Waiting for the button to be clickable.")

                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.b-ultimas__btn"))
                )

                time.sleep(1)

                new_height = self.driver.execute_script("return document.body.scrollHeight")

                # Scroll the button into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)

                if load_more >= self.scroll_limit:
                    logger.debug("Reached scrolls limit: %s", load_more)
                    break

                logger.debug("Loading more content.")
                self.driver.execute_script("arguments[0].click()", load_more_button)

                if new_height != last_height:
                    last_height = new_height
                    load_more += 1

                time.sleep(2)

            except TimeoutException:
                retry_count += 1
                logger.warning("Timeout.")
                continue
            except Exception as ex:
                logger.error("Unexpected error in scroll_page: %s", ex)
                break

    def search(self, link: str, **kwargs) -> None:
        try:
            logger.debug("Crawling link: %s", link)
            self.driver.get(link)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "footer")))
            time.sleep(2)
            # self.accept_cookies()
            # time.sleep(2)
            # self.scroll_page()
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            soup = clean_html(soup)
            elements = soup.find_all("a", href=True)
            hyperlinks = extract_links(elements)

            if len(hyperlinks) == 0:
                logger.error("No links found.")

            self.driver.close()

            hyperlink_list = []

            for hyperlink in hyperlinks:
                try:
                    hyperlink_list.append(
                        Link(
                            title=hyperlink["title"],
                            url=hyperlink["url"],
                            source=link,
                            published_at=hyperlink["published_at"],
                        )
                    )
                except ValueError:
                    logger.error(
                        "Failed to append hyperlink with title '%s' and URL '%s'",
                        hyperlink.get("title", "N/A"),
                        hyperlink.get("url", "N/A"),
                    )
                    continue

            logger.debug("Found %s hyperlinks on '%s'", len(hyperlink_list), link)
            self.model.bulk_insert(hyperlink_list)
        except Exception as ex:
            logger.error("Error while crawling domain %s: %s", link, ex)
            raise
        finally:
            self.driver.close()

    def accept_cookies(self):
        button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='button']"))
        )

        self.driver.execute_script("arguments[0].click()", button)


class CNNBrasilCrawler(BaseSeleniumCrawler):
    model = Link

    def __init__(self, scroll_limit: int = 50) -> None:
        super().__init__(scroll_limit=scroll_limit)

    def scroll_page(self) -> None:
        logger.debug("Start scrolling page.")
        load_more = 0
        page_number = 0
        last_page_number = 0
        repeated_page_count = 0
        retry_count = 0

        timeout_duration = TIMEOUT  # 10 minutes # Record the start time start_time = time.time()
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                logger.debug("Timeout reached. Stopping the crawl.")
                break

            if retry_count > MAX_RETRIES:
                logger.debug("Max retries reached.")
                break

            try:
                logger.debug("Scroll page down.")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script(
                        "return window.pageYOffset + window.innerHeight >= document.body.scrollHeight"
                    )
                )

                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.block-list-get-more-btn"))
                )

                page_number = int(load_more_button.get_attribute("data-limit"))

                if not isinstance(
                    page_number,
                    int,
                ):
                    logger.debug("Invalid page number.")
                    continue

                logger.debug("Current page number: %s", page_number)

                ## Break if the page is not being updated
                if page_number == last_page_number:
                    repeated_page_count += 1
                    logger.warning("Seeing the same page for %s interactions.", repeated_page_count)
                else:
                    repeated_page_count = 0

                if repeated_page_count > MAX_REPEATED_PAGE_COUNT:
                    logger.debug("Skipping, seeing the same page for %s iteractions.", repeated_page_count)
                    break

                if page_number > last_page_number:
                    logger.debug("New content loaded.")
                    load_more += 1
                    last_page_number = page_number
                    if load_more >= self.scroll_limit:
                        break

                logger.debug("Load more content")
                self.driver.execute_script("arguments[0].click()", load_more_button)
                time.sleep(1)

            except TimeoutException:
                retry_count += 1
                logger.warning("Timeout.")
                continue
            except Exception as ex:
                logger.error("Unexpected error in scroll_page: %s", ex)
                break

    def accept_cookies(self):
        button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cookie-banner-lgpd_accept-button"))
        )
        self.driver.execute_script("arguments[0].click()", button)

    def search(self, link: str, **kwargs) -> None:
        try:
            logger.debug("Crawling link: %s", link)
            self.driver.get(link)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "footer")))
            self.scroll_page()
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            soup = clean_html(soup)
            elements = soup.find_all("a", href=True)
            hyperlinks = extract_links(elements)
            self.driver.close()

            hyperlink_list = []
            for hyperlink in hyperlinks:
                try:
                    hyperlink_list.append(
                        Link(
                            title=hyperlink["title"],
                            url=hyperlink["url"],
                            source=link,
                            published_at=hyperlink["published_at"],
                        )
                    )
                except ValueError:
                    logger.error(
                        "Failed to append hyperlink with title '%s' and URL '%s'",
                        hyperlink.get("title", "N/A"),
                        hyperlink.get("url", "N/A"),
                    )
                    continue

            logger.debug("Found %s hyperlinks on '%s'", len(hyperlink_list), link)
            self.model.bulk_insert(hyperlink_list)
        except Exception as ex:
            logger.error("Error while crawling domain %s: %s", link, ex)
            raise
        finally:
            self.driver.close()


class BBCBrasilCrawler(BaseSeleniumCrawler):
    model = Link

    def __init__(self, scroll_limit: int = 40) -> None:
        super().__init__(scroll_limit=scroll_limit)

    def scroll_page(self, tab_list: list) -> None:
        logger.debug("Start scrolling page.")
        load_more = 0
        page_number = 0
        retry_count = 0
        last_page_number = 0

        timeout_duration = TIMEOUT  # 10 minutes # Record the start time start_time = time.time()
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                logger.debug("Timeout reached. Stopping the crawl.")
                break

            if retry_count > MAX_RETRIES:
                logger.debug("Max retries reached.")
                break

            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script(
                        "return window.pageYOffset + window.innerHeight >= document.body.scrollHeight"
                    )
                )

                logger.debug("Waiting for the button to be clickable.")

                next_page_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            "a.focusIndicatorOutlineBlack.bbc-1spja2a[aria-labelledby='pagination-next-page']",
                        )
                    )
                )

                # Extract the href value
                href_value = next_page_element.get_attribute("href")

                # Regular expression to extract the number
                pattern = r"\?page=(\d+)"

                # Search for the pattern in the href string
                match = re.search(pattern, href_value)

                page_number = int(match.group(1))

                if not isinstance(
                    page_number,
                    int,
                ):
                    logger.debug("Invalid page number.")
                    continue

                logger.debug("Page number: %s", page_number)

                if page_number > last_page_number:
                    logger.debug("New content loaded.")
                    load_more += 1
                    last_page_number = page_number
                    if load_more >= self.scroll_limit:
                        logger.debug("Reached scrolls limit: %s", load_more)
                        break

                tab_list.append(self.driver.page_source)

                logger.debug("Loading more content.")
                self.driver.execute_script("arguments[0].click()", next_page_element)
                time.sleep(1)

            except TimeoutException:
                retry_count += 1
                logger.warning("Timeout.")
                continue
            except Exception as ex:
                logger.error("Unexpected error in scroll_page: %s", ex)
                break

    def accept_cookies(self):
        button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cookie-banner-lgpd_accept-button"))
        )
        self.driver.execute_script("arguments[0].click()", button)

    def search(self, link: str, **kwargs) -> None:
        try:
            logger.debug("Crawling link: %s", link)
            self.driver.get(link)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "footer")))

            tab_list = []

            self.scroll_page(tab_list)

            site_elements = []

            for tab in tab_list:
                soup = BeautifulSoup(tab, "html.parser")
                soup = clean_html(soup)
                elements = soup.find_all("a", href=True)
                site_elements.extend(elements)

            hyperlinks = extract_links(site_elements)

            self.driver.close()

            hyperlink_list = []
            for hyperlink in hyperlinks:
                try:
                    hyperlink_list.append(
                        Link(
                            title=hyperlink["title"],
                            url=hyperlink["url"],
                            source=link,
                            published_at=hyperlink["published_at"],
                        )
                    )
                except ValueError:
                    logger.error(
                        "Failed to append hyperlink with title '%s' and URL '%s'",
                        hyperlink.get("title", "N/A"),
                        hyperlink.get("url", "N/A"),
                    )
                    continue

            logger.debug("Found %s hyperlinks on '%s'", len(hyperlink_list), link)
            self.model.bulk_insert(hyperlink_list)
        except Exception as ex:
            logger.error("Error while crawling domain %s: %s", link, ex)
            raise
        finally:
            self.driver.close()
