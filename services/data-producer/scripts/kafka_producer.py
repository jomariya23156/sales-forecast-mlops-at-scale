# NOTE: Using logging is crucial here. Inside Docker, if we chain multiple
# commands (like we did here), print() will only work in the first script execution
import os
import time
import logging
import numpy as np
import pandas as pd
import json
from datetime import datetime
from kafka import KafkaProducer

# look like internally kafka-python also use logging default setting
# but we don't want to see its log and share the logger, so need to create a new one
logger = logging.getLogger("kafka_producer.py")
logger.setLevel(logging.INFO)
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(log_format)
logger.addHandler(ch)


KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sale_rossman_store")
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "kafka:9092")


def preprocess_input_df(df: pd.DataFrame) -> pd.DataFrame:
    # convert all column names into lower case for simplicity]
    df.columns = map(lambda x: x.lower(), df.columns)
    # there are both 0 and '0' in stateholiday, so convert them all to str
    # cuz there are also 'a', 'b', 'c', 'd' so it should be str
    df["stateholiday"] = df["stateholiday"].astype(str)
    # add a dummy item name as an example for extensibility
    df["productname"] = "product_A"
    df = df.sort_values("date", ascending=True).reset_index(drop=True)
    return df


# This is the place where you have to modify the data source to
# your real use case e.g. api, external source, etc. then send
# it to kafka topic using producer
logger.info("Reading a small subset of data for dummy streaming...")
sale_stream = pd.read_csv("datasets/rossmann-store-sales/train_only_last_10d.csv")
sale_stream = preprocess_input_df(sale_stream)

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
    value_serializer=lambda x: json.dumps(x).encode("utf-8"),
)

logger.info("Start streaming data!")
pointer = 0
while True:
    if pointer == len(sale_stream):
        pointer = 0

    # change date to today so it imitates realtime api
    day_sale_row = sale_stream.iloc[pointer]
    day_sale_row["date"] = datetime.now().strftime("%Y-%m-%d")
    day_sale = json.loads(day_sale_row.to_json())
    logger.info(f"Sent: {day_sale}")
    producer.send(topic=KAFKA_TOPIC, value=day_sale)
    producer.flush()

    pointer += 1
    time.sleep(10)  # for demo and develop
    # time.sleep(60) # every 1 min
