# create a Kafka consumer to consume data from producer
# and use Kafka connect to save to Postgres
# (then modify the training service to fetch latest N data rows from Postgres)

import os
import json
from kafka import KafkaConsumer
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'sale_rossman_store')

consumer = KafkaConsumer(
    bootstrap_servers=['kafka:9092'],
    # auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)
print('All available topics:', consumer.topics())
consumer.subscribe(topics=[KAFKA_TOPIC])
print('Confirmed subscription to:',  consumer.subscription())

for message in consumer:
    print("%d:%d: k=%s v=%s" % (message.partition,
                                 message.offset,
                                 message.key,
                                 message.value))