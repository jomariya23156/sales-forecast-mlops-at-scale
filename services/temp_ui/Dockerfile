FROM python:3.9.17-slim

ARG TEMP_UI_PORT=$TEMP_UI_PORT

WORKDIR /service

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY app/ app/

EXPOSE $TEMP_UI_PORT

WORKDIR /service/app

CMD uvicorn main:app --host 0.0.0.0 --port ${TEMP_UI_PORT}