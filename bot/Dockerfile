FROM python:3.10

# install libgl
RUN apt-get update -y && apt-get install libgl1 -y

# install & configure poetry
RUN python3 -m pip install poetry
RUN poetry config virtualenvs.in-project true

# make villager-bot dir
RUN mkdir villager-bot
WORKDIR /villager-bot

# install dependencies
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-dev --no-interaction

# copy over common & bot folders
COPY common common
COPY bot bot

# build tiler.pyx using pyximport
RUN poetry run python3 bot/build_tiler.py

# run Villager Bot cluster
CMD poetry run python3 -m bot
