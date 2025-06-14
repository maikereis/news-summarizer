from pathlib import Path
from typing import List

import typer
import yaml
from pipelines import crawl_news_links, generate_training_dataset, process_documents, scrape_news_articles

app = typer.Typer()


def read_yaml(file_path: Path) -> List[str]:
    with file_path.open("r") as file:
        data = yaml.safe_load(file)
    return data.get("parameters", None).get("links", None)


@app.command()
def crawl_links(yaml_filepath: Path):
    links = read_yaml(yaml_filepath)

    if links is None:
        return

    crawl_news_links(links)


@app.command()
def scrape_content():
    scrape_news_articles()


@app.command()
def process_content():
    process_documents()


@app.command()
def generate_datasets(dataset_type: str):
    generate_training_dataset(dataset_type)


if __name__ == "__main__":
    app()
