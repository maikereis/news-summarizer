import datetime
import logging

from bs4 import BeautifulSoup

from news_summarizer.domain.documents import Article
from news_summarizer.scraper.base import BaseSeleniumScraper

logger = logging.getLogger(__name__)


class G1Scraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        self.driver.get(article_link)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
        if len(self.soup) == 0:
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

    def _extract_title(self, soup: BeautifulSoup):
        title = soup.find("h1", class_="content-head__title").text
        return title

    def _extract_author(self, soup: BeautifulSoup):
        author = soup.find("a", class_="multi_signatures").text
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        subtitle = soup.find("h2", class_="content-head__subtitle").text
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        paragraphs = soup.select("div.mc-article-body p")
        content = "\n".join([p.text for p in paragraphs if len(p) > 0])
        return content

    def _extract_publication_date(self, soup: BeautifulSoup):
        publication_date = soup.find("time", itemprop="datePublished")["datetime"]
        return publication_date


class R7Scraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        self.driver.get(article_link)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
        if len(self.soup) == 0:
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

    def _extract_title(self, soup: BeautifulSoup):
        title = soup.find(
            "h1",
            class_="base-font-primary dark:base-text-neutral-high-400 base-mb-xxxs base-text-xl base-font-semibold base-leading-xxl lg:base-leading-giant lg:base-text-xxl base-text-neutral-low-500",
        ).text
        return title

    def _extract_author(self, soup: BeautifulSoup):
        first_span = soup.find(
            "span",
            class_="article-text-editorial-color article-ml-quark article-mr-quark dark:!article-text-neutral-high-400",
        )
        author = first_span.find_next("span").text
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        subtitle = soup.find(
            "h2",
            class_="base-font-primary dark:base-text-neutral-high-400 base-text-xxs base-font-bold base-leading-md sm:base-text-md sm:base-font-medium sm:base-leading-lg base-text-neutral-low-500",
        ).text
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        article = soup.find("article", class_="b-article-body")
        paragraphs = article.find_all_next("span", class_="b-article-body__text")
        content = "\n".join([p.text for p in paragraphs if len(p) > 0])
        return content

    def _extract_publication_date(self, soup: BeautifulSoup):
        publication_date = soup.find("time", itemprop="datePublished")["datetime"]
        modified_date = soup.find("time", itemprop="dateModified")["datetime"]
        if modified_date is None:
            return publication_date
        return modified_date


class BandScraper(BaseSeleniumScraper):
    model = Article

    def __init__(self) -> None:
        super().__init__()

    def extract(self, article_link: str, **kwargs) -> None:
        self.driver.get(article_link)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
        if len(self.soup) == 0:
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

    def _extract_title(self, soup: BeautifulSoup):
        h1_element = soup.find(
            "h1",
            class_="cs-entry__title",
        )
        title = h1_element.find("span").text
        return title

    def _extract_author(self, soup: BeautifulSoup):
        author = soup.find(
            "span",
            class_="cs-meta-author-name",
        ).text
        return author

    def _extract_subtitle(self, soup: BeautifulSoup):
        subtitle = soup.find(
            "div",
            class_="cs-entry__subtitle",
        ).text
        return subtitle

    def _extract_content(self, soup: BeautifulSoup):
        article = soup.find("div", class_="cs-entry__content-wrap")
        paragraphs = article.find_all("p")
        content = "\n".join([p.text for p in paragraphs if len(p) > 0])
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
        date_string = soup.find("div", class_="cs-meta-date").text
        date_string = self._translate_months(date_string)
        date_format = "%B %d, %Y"
        publication_date = datetime.strptime(date_string, date_format)
        return publication_date
