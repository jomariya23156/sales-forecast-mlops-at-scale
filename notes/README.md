# Table of contents
- [Notes I took during the development](#notes-i-took-during-the-development)
  - [Forecast models training and retraining strategy](#forecast-models-training-and-retraining-strategy)
  - [Kafka Docker Compose and Helm](#kafka-docker-compose-and-helm)
  - [Stream processing options](#stream-processing-options)
  - [My thoughts about Ray's training jobs submission](#my-thoughts-about-rays-training-jobs-submission)
  - [Using Ray with external Redis (in Docker Compose)](#using-ray-with-external-redis-in-docker-compose)
  - [Modifications made to Airflow docker-compose](#modifications-made-to-airflow-docker-compose)


# Notes I took during the development
Nothing important here, but might be worth reading in case you're wondering about some of my system design choices or some fine-grained details I have made along the way.

## Forecast models training and retraining strategy
First of all, demand forecasting is not my domain expertise and the performance of the model is not the main focus of this project anyway. Here's the approach I've learned and used.
- Pull the last 4 months' data to train a new forecaster from scratch (using .fit as normally)
- Do a Walk-Forward (anchored) cross-validation strategy with `n_splits=5` and compute the average metrics.
- Train a final model using all pulled data
- All models are retrained *WEEKLY* (1,115 models in this project) to predict the next week's sales.
- Users can also trigger retraining a specific model from UI *AT ANY TIME*.

**Note on options**
- This approach loses the benefit of the initial model which could be trained on the full dataset
- But if the drift is concerned, it’s worthwhile
- Other approaches that can leverage historical knowledge
    - Transfer learning (for DL-based models)
    - Ensemble models (full and windowed models)
    - OR you can schedule a model training with the full dataset less frequently like every month and train the windowed model more frequently like every week in this case
- Another valid option is incremental learning which uses the old trained model to just learn new data (data for the last week in our case). It’s empirical and requires experiments to answer.

## Kafka Docker Compose and Helm
Kafka services on Docker Compose and Halm are different in settings, mainly in Docker Compose, we use KRaft for config management (which is newer). But in Helm, we use ZooKeeper because, honestly, I'm not managed to pull it off with KRaft, sorry :'( (It's quite complex).

## Stream processing options
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
    - Scalable and efficient (with the nature of distributed computing systems)
    - Can handle complex data transformation at scale

    Cons:
    - Another tool to learn (make the learning curve for the project steeper)
3. Kafka Connect -> Plugin tool from Kafka to connect to external tools to receive or send messages (source or sink connectors in Kafka terms)

    Pros:
    - Support Kafka natively (of course)
    - Might be the fastest option of all
    - Suitable for straightforward receiving and sending messages to external tools

    Cons:
    - Limited control over data transformation
    - On its own, the usage and setup are not quite intuitive and no Python API (at the time of writing)
    - Docs are limited and most of the resources online go for hosted services offered by other venders (e.g. Confluent, Aiven)
    - Which led to vendor-lockon option and limited usage due to the license

So in this project, **I went for the 2nd option**, Stream processing framework, with **Spark Streaming** since I feel like this is a good balance between performance and control. And if in the future, I need to do some more complex data stream transformation, this is gonna be pretty much a go-to option and I can come back to look it up from this project.

## My thoughts about Ray's training jobs submission
You can submit the training jobs directly from **ANY** service in the same network. For example, you can submit the training jobs from Streamlit UI (to train a single model on-demand) or from Airflow through DAG (to train all models). However, I choose to have another FastAPI app as a middleman to handle this job submission instead. My reasons are:
- Better separation of concern: To submit any Ray task, the file for task execution must be available LOCALLY from the client. Meaning if you want to submit a training task from UI, your Streamlit needs to hold your training script, the same thing for Airflow. With FastAPI as a middleman, you can store all required files in a single server and you make sure any one component in the whole system serves one purpose.
- Easier to maintain: Following the previous point, it makes your life a lot harder to maintain the services. For example, without a FastAPI middleman, if you need to update the logic for training, you have to update both Streamlit and Airflow.
- Offer more flexibility and customizability: With my approach, you can add as many extra steps as you like to handle and process incoming Ray job submission requests from clients. For example, you can include more authentication steps for security purposes.

## Using Ray with external Redis (in Docker Compose)
If we restart the Ray container, all previous job history will be gone because Ray stores them in-memory only. We can add an external Redis to manage these variables. However, this seems very very unstable. This is also stated in the official doc that using external Redis supports only on-cloud / Kubernetes. But I want to try and... from time-to-time during the development, I found that the Ray cluster does not accept the Job submission and throws the error `Job supervisor actor could not be scheduled: The actor is not schedulable: The node specified via NodeAffinitySchedulingStrategy doesn't exist any more or is infeasible, and soft=False was specified.` I could fix that by removing all data in Redis by running `docker-compose exec redis redis-cli FLUSHALL` AND/OR removing Ray container and rebuilding it again. But it's annoying and time-consuming. So in the end, I got rid of external Redis for Ray, Bye~.

## Modifications made to Airflow docker-compose
- Removed postgres service (connect to our existing with new username and pwd)
- Added an env variable `SPARK_STREAM_CHECKPOINTS_PATH` and mounted a Docker volume for its checkpoint
- Connected to `forecast_network` defined in our existing docker-compose
- Note when starting: need to specify both compose files i.e. `docker-compose -f docker-compose.yml -f docker-compose-airflow.yml` from doc: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
