# sales-forecast-mlops-at-scale

Scalable End-to-end MLOps system for sales forecasting.

dataset: https://www.kaggle.com/datasets/pratyushakar/rossmann-store-sales

*Note*: Remove `services/training_service/kaggle.json` in the next commit.

Original docker-compose file: https://airflow.apache.org/docs/apache-airflow/2.8.3/docker-compose.yaml
Modification made:
- Removed postgres (connect to our existing with new username and pwd)
- Added env variable `SPARK_STREAM_CHECKPOINTS_PATH` and mount volume for this checkpoint
- Connect to `forecast_network` defined in our existing docker-compose
- Note when starting: need to specify both compose files i.e. `docker-compose -f docker-compose.yml -f docker-compose-airflow.yml`
From doc: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

### Note on Stream processing options
There are a few options we can do to consume the stream data from Kafka producer and save to Postgres
1. Dead and simple consumer with SQLAlchemy
    - Consume the message from a topic with KafkaConsumer class
    - Mannually use SQLAlchemy to save the new data into Postgres  

    Pros:
    - Easy and Straightforward
    - Very Pythonic

    Cons:
    - Not really scalable by nature (need careful coding and designing to make sure of this)
    - Might cause a bottleneck in the process
2. Use Steam processing frameworks such as Spark Streaming or Apache Flink

    Pros:
    - Support Kafka out-of-the-box
    - Scalable and efficient (with the nature of distributed computing system)
    - Can handle complex data tranformation at scale

    Cons:
    - Another tool to learn (make the learning curve for the project steeper)
3. Kafka Connect -> Plugin tool from Kafka to connect to external tools to receive or send message (source or sink connectors in Kafka terms) 

    Pros:
    - Support Kafka natively (of course)
    - Might be the fastest option of all
    - Suitable for straightforward receiving and sending message to external tools

    Cons:
    - Limited control over data transformation
    - By it own, the usage and setup is not quite intuitive and no Python API (at the time of writing)
    - Docs are limited and most of the resources online go for hosted service offered by other venders (e.g. Confluent, Aiven)
    - Which led to vendor-lockon option and limited usage due to the license

So in this project, **I went for 2nd option**, Stream processing framework, with **Spark Streaming** since I feel like this is good balance between performance and control. And if in the future, I need to do some more complex data stream transformation, this is a pretty much go-to option and I can come back to look it up from this project.