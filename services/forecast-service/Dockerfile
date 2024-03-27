FROM python:3.9.17-slim

ARG FORECAST_SERVICE_PORT=$FORECAST_SERVICE_PORT

COPY requirements.txt /service/requirements.txt

RUN pip install -r /service/requirements.txt

COPY app/ /service/app/

EXPOSE $FORECAST_SERVICE_PORT

WORKDIR /service/app

CMD gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${FORECAST_SERVICE_PORT}