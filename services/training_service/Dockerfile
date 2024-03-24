FROM python:3.9.17-slim

ARG TRAINING_SERVICE_PORT=$TRAINING_SERVICE_PORT

# there is a pip package required psutil which requires gcc included in build-essential here
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        git \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /service/requirements.txt

RUN pip install -r /service/requirements.txt

COPY app/ /service/app/

EXPOSE $TRAINING_SERVICE_PORT

WORKDIR /service/app

CMD gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${TRAINING_SERVICE_PORT}