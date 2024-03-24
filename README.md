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

## Service port:
MLflow: 5050
Airflow: 8080
Ray Dashboard: 8265
Redis: 6379
Nginx: 80

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

### Note on my thought about Ray training jobs submission
In fact, you can submit the training jobs directly from **ANY** service in the same network. For example, you can submit the training jobs form Streamlit UI (to train a single model on-demand) or from Airflow through DAG (to train all models). But I choose to have another FastAPI app as a middle man to handle this job submission instead. My reasons are:
- Better separation of concern: In order to submit any Ray task, the file for task execution must be available LOCALLY from the client. Meaning if you want to submit a training task from UI, your Streamlit needs to hold your training script, same thing for Airflow. With FastAPI as a middle man, you can store all required files in a single server and you make sure any one component in the whole system serve one purpose.
- Easier to maintain: Following the previous point, it makes your life a lot harder to maintain the services. For example, without FastAPI middle man, if you need to update the logic for training, you have to update both Streamlit and Airflow.
- Offer more flexibility and customizability: With my approach, you can add as many extra steps as you like to handle and process incoming Ray job submission from client. For example, you can include more an authentication step for security purpose.


### Using Ray with external Redis
If we restart the Ray container, all previous job history will be gone because Ray store them in-memory only. We can add an external Redis to manage these variables but, from using, this seems very very unstable, this is also stated in the official doc that using external Redis supports only on-cloud / Kubernetes. But I wanna try and... from time-to-time during the development, I found that the Ray cluster do not accept the Job submission and show error `Job supervisor actor could not be scheduled: The actor is not schedulable: The node specified via NodeAffinitySchedulingStrategy doesn't exist any more or is infeasible, and soft=False was specified.`. I could fix that by removing all data in redis by running `docker-compose exec redis redis-cli FLUSHALL` AND/OR removing Ray container and rebuild it again. But it's annoying and time consuming. So in the end, I got rid of external Redis for Ray, Bye~.
