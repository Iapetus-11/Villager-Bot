FROM python:3.10

# install & configure poetry
RUN python3 -m pip install poetry
RUN poetry config virtualenvs.in-project true

# install dependencies
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-dev --no-interaction

# copy over common & bot folders
COPY common common
COPY bot bot

# run Villager Bot cluster
CMD ["poetry", "run", "python3", "-m", "bot"]
