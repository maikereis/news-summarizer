from typing import Generator

import torch


def batch(list_: list, size: int) -> Generator[list, None, None]:
    yield from (list_[i : i + size] for i in range(0, len(list_), size))


def device_selector() -> str:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return device


def batch_size_selector():
    pass


def clean_html(soup):
    # Remove style and script elements
    for tag in soup(["style", "script"]):
        tag.decompose()
    return soup
