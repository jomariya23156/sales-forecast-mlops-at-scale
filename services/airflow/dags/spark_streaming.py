# create a Kafka consumer to consume data from producer
# and use Kafka connect to save to Postgres
# (then modify the training service to fetch latest N data rows from Postgres)

# need sudo apt update && sudo apt install default-jre-headless

import os
import json
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType
from pyspark.sql.functions import from_json, col
from db_utils import prepare_db

SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_JDBC_CONNECTION_URL = os.getenv(
    "POSTGRES_JDBC_CONNECTION_URL",
    f"jdbc:postgresql://postgres:{POSTGRES_PORT}/spark_pg_db",
)
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sale_rossman_store")
SPARK_STREAM_CHECKPOINTS_PATH = os.getenv(
    "SPARK_STREAM_CHECKPOINTS_PATH", "/home/airflow/spark_streaming_checkpoints"
)
POSTGRES_PROPERTIES = {
    "user": "spark_user",
    "password": "SuperSecurePwdHere",
    "driver": "org.postgresql.Driver",
}


def create_spark_session() -> SparkSession:
    spark = (
        SparkSession.builder.appName("PySpark to Postgres")
        .config(
            "spark.jars.packages",
            "org.postgresql:postgresql:42.5.4,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
        )
        .getOrCreate()
    )
    print("Created a Spark session successfully")
    return spark


def create_df_from_kafka(spark_session) -> DataFrame:
    df = (
        spark_session.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )
    return df


def process_df(df) -> DataFrame:
    schema = StructType(
        [
            StructField("store", IntegerType(), True),
            StructField("dayofweek", IntegerType(), True),
            StructField("date", DateType(), True),
            StructField("sales", IntegerType(), True),
            StructField("customers", IntegerType(), True),
            StructField("open", IntegerType(), True),
            StructField("promo", IntegerType(), True),
            StructField("stateholiday", StringType(), True),
            StructField("schoolholiday", StringType(), True),
            StructField("productname", StringType(), True),
        ]
    )
    processed_df = (
        df.selectExpr("CAST(value AS STRING)")
        .select(from_json(col("value"), schema).alias("data"))
        .select("data.*")
    )
    return processed_df


def write_df_to_db(processed_df):
    query = (
        processed_df.writeStream.foreachBatch(
            lambda batch_df, batch_id: (
                batch_df.write.jdbc(
                    POSTGRES_JDBC_CONNECTION_URL,
                    SALES_TABLE_NAME,
                    "append",
                    properties=POSTGRES_PROPERTIES,
                )
            )
        )
        .trigger(once=True)
        .option(
            "checkpointLocation", SPARK_STREAM_CHECKPOINTS_PATH
        )  # set checkpoints so pyspark won't reread the same messages
        .start()
    )
    return query.awaitTermination()


def stream_kafka_to_db():
    prepare_db()  # create table if not exist
    print("Creating Spark session with Kafka and Postgres packages")
    spark = create_spark_session()
    df = create_df_from_kafka(spark)
    processed_df = process_df(df)
    print("Processed Spark DataFrame")
    write_df_to_db(processed_df)
    print("Successfully streamed Kafka to Postgres with Spark Streaming!")
