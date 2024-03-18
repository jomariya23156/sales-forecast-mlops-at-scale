# base Airflow image
FROM apache/airflow:2.8.3-python3.9 

USER root

# Install jre for spark plugins
RUN apt-get update && apt-get install -y default-jre-headless

USER airflow

# Install Spark dependencies
RUN pip install pyspark==3.5.1 SQLAlchemy==1.4.49