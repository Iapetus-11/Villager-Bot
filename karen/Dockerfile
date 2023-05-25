FROM python:3.10-slim-buster AS build

WORKDIR /build

RUN apt-get update -y
RUN apt-get install -y --no-install-recommends gcc python3-dev

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml /build/pyproject.toml
COPY poetry.lock /build/poetry.lock

RUN poetry install --no-root --without dev

FROM python:3.10-slim-buster

WORKDIR /villager-bot

COPY --from=build /build/.venv/ /villager-bot/.venv/

COPY common /villager-bot/common/
COPY karen /villager-bot/karen/

CMD [".venv/bin/python3", "-m", "karen"]
