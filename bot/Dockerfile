FROM python:3.10-slim-bookworm AS build

WORKDIR /build

RUN apt-get update -y
RUN apt-get install -y --no-install-recommends ca-certificates gcc python3-dev

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml /build/pyproject.toml
COPY poetry.lock /build/poetry.lock

RUN poetry install --no-root --without dev

COPY common common
COPY bot bot

#RUN poetry run python3 -m bot --build-cython-only

FROM python:3.10-slim-bookworm

# TODO: I would like to figure out how to build the cython portion of Villager Bot in the build stage
# Unfortunately, it does not work properly so I have to install gcc again here
# Require the Bookworm CA update that distrusts the compromised eMudhra chain.
RUN apt-get update -y \
    && apt-get install -y ca-certificates gcc ffmpeg \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' ca-certificates)" ge '20250419~deb12u2' \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /villager-bot

COPY --from=build /build/.venv/ /villager-bot/.venv/

COPY common /villager-bot/common/
COPY bot /villager-bot/bot/

CMD [".venv/bin/python3", "-m", "bot"]
