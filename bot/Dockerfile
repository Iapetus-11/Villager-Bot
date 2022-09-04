FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED=TRUE

# install essential packages
RUN apt-get update -y
RUN apt-get install -y git build-essential libgl1 libglib2.0-0

# install & configure poetry
RUN python3 -m pip install poetry --no-cache-dir
RUN poetry config virtualenvs.in-project true

# make villager-bot dir
RUN mkdir villager-bot
WORKDIR /villager-bot

# install dependencies
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-dev --no-interaction

# copy over common and bot folders
COPY common common
COPY bot bot

# build cython extensions
RUN poetry run python3 -m bot --build-cython-only

# run Villager Bot cluster
CMD poetry run python3 -m bot
