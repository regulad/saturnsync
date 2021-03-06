# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /app

COPY . .

RUN pip3 install poetry
RUN poetry install

CMD [ "poetry", "run", "python", "./main.py"]
