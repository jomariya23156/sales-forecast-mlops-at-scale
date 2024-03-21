from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from spark_streaming import stream_kafka_to_db

with DAG(
    dag_id="kafka_spark_db_dag",
    default_args={
        "owner": "jom_ariya",
        "depends_on_past": False,
        "email": ["jom_example@gmail.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Read data from the Kafka topic and save to Postgres",
    schedule_interval=timedelta(days=1),  # run daily
    start_date=datetime.now(),
    catchup=False,
    tags=["spark_streaming", "kafka", "postgres"],
) as dag:

    kafka_spark_to_db_task = PythonOperator(
        task_id="kafka_spark_to_db", python_callable=stream_kafka_to_db
    )
