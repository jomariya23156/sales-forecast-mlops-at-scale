# script to delete the kafka topic
import os
from kafka import KafkaAdminClient

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sale_rossman_store")
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "kafka:9092")

admin = KafkaAdminClient(
    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
)

admin.delete_topics([KAFKA_TOPIC])
print(f"Deleted {KAFKA_TOPIC} topic")
