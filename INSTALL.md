## News Summarizer – Installation Guide

This guide will help you set up the News Summarizer project locally using pyenv, poetry, and Docker. Follow the steps below to get started.

### 1. Prerequisites

Before proceeding, ensure you have the following tools installed:

[pyenv](https://github.com/pyenv/pyenv) – Python version management

[Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) – Dependency management and packaging

[Docker](https://docs.docker.com/engine/install/) – Containerization platform

[Docker Compose](https://docs.docker.com/compose/install/linux/) – Tool for defining and running multi-container Docker applications

### 2.Installation Steps

## 1. Install Project Dependencies

Install the project dependencies defined in pyproject.toml:
```bash
poetry install
```

## 2. Start the Services Using Docker Compose

Ensure Docker and Docker Compose are installed and running. Then, start the services:

```bash
docker compose up
```
