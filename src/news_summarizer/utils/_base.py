import time
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


class RateCalculator:
    def __init__(self) -> None:
        self._start_time = None
        self._counter = None

    def _calculate_rate(self):
        current_time = time.time()
        duration = current_time - self._start_time  # Calculate the duration in seconds
        rate = self._counter / (duration / 60)  # Calculate the rate (task per minute)
        return rate
