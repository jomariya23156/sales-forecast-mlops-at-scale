# create a Kafka consumer to consume data from producer
import os
import json
from kafka import KafkaConsumer

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sale_rossman_store")
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "kafka:9092")

consumer = KafkaConsumer(
    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
    # auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)
print("All available topics:", consumer.topics())
consumer.subscribe(topics=[KAFKA_TOPIC])
print("Confirmed subscription to:", consumer.subscription())

for message in consumer:
    print(
        "%d:%d: k=%s v=%s"
        % (message.partition, message.offset, message.key, message.value)
    )
