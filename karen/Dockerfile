FROM python:3.13-slim-bookworm AS build

WORKDIR /build

RUN apt-get update -y
RUN apt-get install -y --no-install-recommends gcc python3-dev

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml /build/pyproject.toml
COPY poetry.lock /build/poetry.lock

RUN poetry install --no-root --without dev

FROM python:3.13-slim-bookworm

WORKDIR /villager-bot

COPY --from=build /build/.venv/ /villager-bot/.venv/

COPY common /villager-bot/common/
COPY karen /villager-bot/karen/

CMD [".venv/bin/python3", "-m", "karen"]
