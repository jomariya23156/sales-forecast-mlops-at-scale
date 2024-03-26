FROM python:3.9.17-slim

# for mounting datasets in (actually we can just mount without mkdir, 
# but wanna explicitly included here so I don't forget LOL)
RUN mkdir -p /service/datasets

COPY requirements.txt /service/requirements.txt

RUN pip install -r /service/requirements.txt

COPY scripts/ /service/scripts/

WORKDIR /service

CMD ["bash", "-c", "python scripts/put_data_in_postgres.py && python scripts/kafka_producer.py"]