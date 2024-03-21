import os
from kafka import KafkaAdminClient

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sale_rossman_store")

admin = KafkaAdminClient(
    bootstrap_servers=["kafka:9092"],
)

admin.delete_topics([KAFKA_TOPIC])
print(f"Deleted {KAFKA_TOPIC} topic")
