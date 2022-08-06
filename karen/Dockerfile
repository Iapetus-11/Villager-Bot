FROM python:3.10

# setup poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1
RUN python -m pip install poetry

# install dependencies
ADD pyproject.toml .
ADD poetry.lock .
RUN poetry install

# copy over rest of files
WORKDIR /
ADD ./common /common
ADD ./karen /karen

# run karen
CMD ["python", "-m", "karen"]
