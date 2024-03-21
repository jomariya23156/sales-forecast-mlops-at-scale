# split a part of data from real dataset
# and create a new Kafka stream data producer (with time interval) infinite loop
# https://medium.com/@shaantanutripathi/streaming-dummy-data-to-kafka-f94a3baef57b

import os
import time
import numpy as np
import pandas as pd
import json
from datetime import datetime
from kafka import KafkaProducer

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sale_rossman_store")


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


sale_stream = pd.read_csv("datasets/rossmann-store-sales/train_only_last_10d.csv")
sale_stream = preprocess_input_df(sale_stream)

producer = KafkaProducer(
    bootstrap_servers=["kafka:9092"],
    value_serializer=lambda x: json.dumps(x).encode("utf-8"),
)

pointer = 0
while True:
    if pointer == len(sale_stream):
        pointer = 0

    # change date to today so it imitates realtime api
    day_sale_row = sale_stream.iloc[pointer]
    day_sale_row["date"] = datetime.now().strftime("%Y-%m-%d")
    day_sale = json.loads(day_sale_row.to_json())
    print("Sent:", day_sale)
    producer.send(topic=KAFKA_TOPIC, value=day_sale)
    producer.flush()

    pointer += 1
    time.sleep(10)
    # time.sleep(60*5) # every 5 mins
