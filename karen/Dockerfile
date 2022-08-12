FROM python:3.10-slim-buster

# install git
RUN apt-get update -y
RUN apt-get install -y git build-essential

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

# copy over common and karne folders
COPY common common
COPY karen karen

# run karen
CMD poetry run python3 -m karen
