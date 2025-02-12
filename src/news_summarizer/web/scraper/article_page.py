import datetime
import logging
import warnings

from bs4 import BeautifulSoup

from news_summarizer.domain.documents import Article
from news_summarizer.utils import clean_html

from urllib3 import HTTPConnectionPool
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException

from .base import BaseSeleniumScraper

logger = logging.getLogger(__name__)


class G1Scraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        try:
            logger.info("Start scraping link: %s.", article_link)
            self.driver.get(article_link)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
            if (len(self.soup) == 0) or (self.soup is None):
                raise ValueError("No elements scraped from link %s", article_link)

            title = self._extract_title(self.soup)
            author = self._extract_author(self.soup)
            subtitle = self._extract_subtitle(self.soup)
            content = self._extract_content(self.soup)
            publication_date = self._extract_publication_date(self.soup)

            intance = self.model(
                title=title,
                subtitle=subtitle,
                author=author,
                content=content,
                publication_date=publication_date,
                url=article_link,
            )

            intance.save()

        except ValueError as ve:
            logger.error("Value error scraping link %s: %s", article_link, ve)
        except InvalidSessionIdException as ise:
            logger.error("Timeout while scraping link %s: %s", article_link, ise)
        except HTTPConnectionPool as hcp_ex:
            logger.error("HTTP error while scraping link %s: %s", article_link, hcp_ex)
        except Exception as ex:
            logger.error("Error while scraping link %s: %s", article_link, ex)
            raise  # Re-raise if you want to propagate the original exception
        finally:
            try:
                self.driver.close()
            except Exception as close_error:
                logger.warning("Error closing the driver: %s", close_error)

    def _extract_title(self, soup: BeautifulSoup):
        try:
            title = soup.find("h1", class_="content-head__title").text
        except AttributeError as at:
            logger.error("Error trying to extract title, %s", at)
            raise ValueError("Error trying to extract title") from at
        return title

    def _extract_author(self, soup: BeautifulSoup):
        try:
            author = soup.find("a", class_="multi_signatures").text
        except AttributeError as at:
            logger.warning("Can't extract author, %s", at)
            return None
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        try:
            subtitle = soup.find("h2", class_="content-head__subtitle").text
        except AttributeError as at:
            logger.warning("Can't extract subtitle, %s", at)
            return None
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        try:
            paragraphs = soup.select("div.mc-article-body p")
            content = "\n".join([p.text for p in paragraphs if len(p) > 0])
        except AttributeError as at:
            logger.error("Error trying to extract content, %s", at)
            raise ValueError("Error trying to extract content") from at
        return content

    def _extract_publication_date(self, soup: BeautifulSoup):
        try:
            publication_date = soup.find("time", itemprop="datePublished")["datetime"]
        except AttributeError as at:
            logger.warning("Can't extract publication date, %s", at)
            return None
        return publication_date


class R7Scraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        try:
            logger.info("Start scraping link: %s.", article_link)
            self.driver.get(article_link)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
            if (len(self.soup) == 0) or (self.soup is None):
                raise ValueError("No elements scraped from link %s", article_link)

            title = self._extract_title(self.soup)
            author = self._extract_author(self.soup)
            subtitle = self._extract_subtitle(self.soup)
            content = self._extract_content(self.soup)
            publication_date = self._extract_publication_date(self.soup)

            intance = self.model(
                title=title,
                subtitle=subtitle,
                author=author,
                content=content,
                publication_date=publication_date,
                url=article_link,
            )

            intance.save()

        except ValueError as ve:
            logger.error("Value error scraping link %s: %s", article_link, ve)
        except InvalidSessionIdException as ise:
            logger.error("Timeout while scraping link %s: %s", article_link, ise)
        except HTTPConnectionPool as hcp_ex:
            logger.error("HTTP error while scraping link %s: %s", article_link, hcp_ex)
        except Exception as ex:
            logger.error("Error while scraping link %s: %s", article_link, ex)
            raise  # Re-raise if you want to propagate the original exception
        finally:
            try:
                self.driver.close()
            except Exception as close_error:
                logger.warning("Error closing the driver: %s", close_error)

    def _extract_title(self, soup: BeautifulSoup):
        try:
            title = soup.find(
                "h1",
                class_="base-font-primary dark:base-text-neutral-high-400 base-mb-xxxs base-text-xl base-font-semibold base-leading-xxl lg:base-leading-giant lg:base-text-xxl base-text-neutral-low-500",
            ).text
        except AttributeError as at:
            logger.error("Error trying to extract title, %s", at)
            raise ValueError("Error trying to extract title") from at
        return title

    def _extract_author(self, soup: BeautifulSoup):
        try:
            first_span = soup.find(
                "span",
                class_="article-text-editorial-color article-ml-quark article-mr-quark dark:!article-text-neutral-high-400",
            )
            author = first_span.find_next("span").text
        except AttributeError as at:
            logger.error("Error trying to extract author, %s", at)
            return None
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        try:
            subtitle = soup.find(
                "h2",
                class_="base-font-primary dark:base-text-neutral-high-400 base-text-xxs base-font-bold base-leading-md sm:base-text-md sm:base-font-medium sm:base-leading-lg base-text-neutral-low-500",
            ).text
        except AttributeError as at:
            logger.warning("Can't extract subtitle, %s", at)
            return None
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        try:
            article = soup.find("article", class_="b-article-body")
            paragraphs = article.find_all_next("span", class_="b-article-body__text")
            content = "\n".join([p.text for p in paragraphs if len(p) > 0])
        except AttributeError as at:
            logger.error("Error trying to extract content, %s", at)
            raise ValueError("Error trying to extract content") from at
        return content

    def _extract_publication_date(self, soup: BeautifulSoup):
        try:
            publication_date = soup.find("time", itemprop="datePublished")["datetime"]
            modified_date = soup.find("time", itemprop="dateModified")["datetime"]
            if modified_date is None:
                return publication_date
        except AttributeError as at:
            logger.warning("Can't extract publication date, %s", at)
            return None
        return modified_date


class BandScraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        try:
            logger.info("Start scraping link: %s.", article_link)
            self.driver.get(article_link)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
            if (len(self.soup) == 0) or (self.soup is None):
                raise ValueError("No elements scraped from link %s", article_link)

            title = self._extract_title(self.soup)
            author = self._extract_author(self.soup)
            subtitle = self._extract_subtitle(self.soup)
            content = self._extract_content(self.soup)
            publication_date = self._extract_publication_date(self.soup)

            intance = self.model(
                title=title,
                subtitle=subtitle,
                author=author,
                content=content,
                publication_date=publication_date,
                url=article_link,
            )

            intance.save()

        except ValueError as ve:
            logger.error("Value error scraping link %s: %s", article_link, ve)
        except InvalidSessionIdException as ise:
            logger.error("Timeout while scraping link %s: %s", article_link, ise)
        except HTTPConnectionPool as hcp_ex:
            logger.error("HTTP error while scraping link %s: %s", article_link, hcp_ex)
        except Exception as ex:
            logger.error("Error while scraping link %s: %s", article_link, ex)
            raise  # Re-raise if you want to propagate the original exception
        finally:
            try:
                self.driver.close()
            except Exception as close_error:
                logger.warning("Error closing the driver: %s", close_error)

    def _extract_title(self, soup: BeautifulSoup):
        try:
            h1_element = soup.find(
                "h1",
                class_="cs-entry__title",
            )
            title = h1_element.find("span").text
        except AttributeError as at:
            logger.error("Error trying to extract title, %s", at)
            raise ValueError("Error trying to extract title") from at
        return title

    def _extract_author(self, soup: BeautifulSoup):
        try:
            author = soup.find(
                "span",
                class_="cs-meta-author-name",
            ).text
        except AttributeError as at:
            logger.info("Can't extract author, %s", at)
            return None
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        try:
            subtitle = soup.find(
                "div",
                class_="cs-entry__subtitle",
            ).text
        except AttributeError as at:
            logger.warning("Can't extract subtitle, %s", at)
            return None
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        try:
            article = soup.find("div", class_="cs-entry__content-wrap")
            paragraphs = article.find_all("p")
            content = "\n".join([p.text for p in paragraphs if len(p) > 0])
        except AttributeError as at:
            logger.error("Error trying to extract content, %s", at)
            raise ValueError("Error trying to extract content") from at
        return content

    def _translate_months(self, date_str: str):
        months_dict = {
            "janeiro": "January",
            "fevereiro": "February",
            "março": "March",
            "abril": "April",
            "maio": "May",
            "junho": "June",
            "julho": "July",
            "agosto": "August",
            "setembro": "September",
            "outubro": "October",
            "novembro": "November",
            "dezembro": "December",
        }

        # Traduz o nome do mês para inglês
        for month_pt, month_en in months_dict.items():
            date_str = date_str.replace(month_pt, month_en)

        return date_str

    def _extract_publication_date(self, soup: BeautifulSoup):
        try:
            date_string = soup.find("div", class_="cs-meta-date").text
            date_string = self._translate_months(date_string)
            date_format = "%B %d, %Y"
            publication_date = datetime.datetime.strptime(date_string, date_format)
        except AttributeError as at:
            logger.warning("Can't extract publication date, %s", at)
            return None
        return publication_date


class BBCBrasilScraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        try:
            logger.info("Start scraping link: %s.", article_link)
            self.driver.get(article_link)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
            self.soup = clean_html(self.soup)

            if not self.soup or not len(self.soup):
                raise ValueError(f"No elements scraped from link {article_link}")

            title = self._extract_title(self.soup)
            author = self._extract_author(self.soup)
            subtitle = self._extract_subtitle(self.soup)
            content = self._extract_content(self.soup)
            publication_date = self._extract_publication_date(self.soup)

            instance = self.model(
                title=title,
                subtitle=subtitle,
                author=author,
                content=content,
                publication_date=publication_date,
                url=article_link,
            )
            return instance

        except ValueError as ve:
            logger.error("Value error scraping link %s: %s", article_link, ve)
        except InvalidSessionIdException as ise:
            logger.error("Timeout while scraping link %s: %s", article_link, ise)
        except HTTPConnectionPool as hcp_ex:
            logger.error("HTTP error while scraping link %s: %s", article_link, hcp_ex)
        except Exception as ex:
            logger.error("Error while scraping link %s: %s", article_link, ex)
            raise  # Re-raise if you want to propagate the original exception
        finally:
            try:
                self.driver.close()
            except Exception as close_error:
                logger.warning("Error closing the driver: %s", close_error)

    def _extract_title(self, soup: BeautifulSoup):
        try:
            return soup.find("h1", class_="bbc-14gqcmb e1p3vdyi0").text
        except AttributeError as e:
            logger.error("Error extracting title: %s", e)
            raise ValueError("Title not found") from e

    def _extract_author(self, soup: BeautifulSoup):
        try:
            return soup.find("span", class_="bbc-1ypcc2").text
        except AttributeError as at:
            logger.warning("Can't extract author, %s", at)
            return None

    def _extract_subtitle(self, soup: BeautifulSoup):
        try:
            return soup.find("span", attrs={"data-testid": "caption-paragraph"}).text
        except AttributeError as at:
            logger.warning("Can't extract subtitle, %s", at)
            return None

    def _extract_content(self, soup: BeautifulSoup):
        try:
            paragraphs = soup.find_all("div", class_="bbc-19j92fr ebmt73l0")
            return "\n".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
        except AttributeError as e:
            logger.error("Error extracting content: %s", e)
            raise ValueError("Content not found") from e

    def _extract_publication_date(self, soup: BeautifulSoup):
        try:
            return soup.find("time", class_="bbc-1dafq0j e1mklfmt0")["datetime"]
        except (AttributeError, TypeError):
            logger.warning("Can't extract publication date, %s", at)
            return None


class CNNBrasilScraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        try:
            logger.info("Start scraping link: %s.", article_link)
            self.driver.get(article_link)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

            if not self.soup or not len(self.soup):
                raise ValueError(f"No elements scraped from link {article_link}")

            title = self._extract_title(self.soup)
            author = self._extract_author(self.soup)
            subtitle = self._extract_subtitle(self.soup)
            content = self._extract_content(self.soup)
            publication_date = self._extract_publication_date(self.soup)

            instance = self.model(
                title=title,
                subtitle=subtitle,
                author=author,
                content=content,
                publication_date=publication_date,
                url=article_link,
            )

            return instance

        except ValueError as ve:
            logger.error("Value error scraping link %s: %s", article_link, ve)
        except InvalidSessionIdException as ise:
            logger.error("Timeout while scraping link %s: %s", article_link, ise)
        except HTTPConnectionPool as hcp_ex:
            logger.error("HTTP error while scraping link %s: %s", article_link, hcp_ex)
        except Exception as ex:
            logger.error("Error while scraping link %s: %s", article_link, ex)
            raise  # Re-raise if you want to propagate the original exception
        finally:
            try:
                self.driver.close()
            except Exception as close_error:
                logger.warning("Error closing the driver: %s", close_error)

    def _extract_title(self, soup: BeautifulSoup):
        try:
            title = soup.find("h1", class_="single-header__title").text
        except AttributeError as at:
            logger.error("Error trying to extract title, %s", at)
            raise ValueError("Error trying to extract title") from at
        return title

    def _extract_author(self, soup: BeautifulSoup):
        try:
            author_element = soup.find("span", class_="author__group")
            author = author_element.find("a").text
        except AttributeError as at:
            logger.warning("Can't extract author, %s", at)
            return None
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        try:
            subtitle = soup.find("p", class_="single-header__excerpt").text
        except AttributeError as at:
            logger.warning("Can't extract subtitle, %s", at)
            return None
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        try:
            paragraphs = soup.select("div.single-content p")
            content = "\n".join([p.text for p in paragraphs if len(p) > 0])
        except AttributeError as at:
            logger.error("Error trying to extract content, %s", at)
            raise ValueError("Error trying to extract content") from at
        return content

    def _extract_publication_date(self, soup: BeautifulSoup):
        try:
            time_element = soup.find("time", class_="single-header__time")
            time_text = time_element.text.strip()

            # Check if "Atualizado" is present in the text
            if "Atualizado" in time_text:
                date_text = time_text.split("|")[1].strip().replace("Atualizado ", "")
            else:
                date_text = time_text.split("|")[0].strip()

            # Convert the date text to a datetime object
            date_format = "%d/%m/%Y às %H:%M"
            publication_date = datetime.datetime.strptime(date_text, date_format)

        except AttributeError as at:
            logger.warning("Can't extract publication date, %s", at)
            return None
        return publication_date
