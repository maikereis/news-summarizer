from pathlib import Path
from typing import List

import typer
import yaml
from pipelines import crawl, generate, index_data, scrap

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

    crawl(links)


@app.command()
def scrap_links():
    scrap()


@app.command()
def index_articles():
    index_data()


@app.command()
def generate_datasets():
    generate()


if __name__ == "__main__":
    app()
