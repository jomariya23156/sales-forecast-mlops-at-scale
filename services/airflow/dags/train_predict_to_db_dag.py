from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from spark_streaming import stream_kafka_to_db

with DAG(
    dag_id="train_predict_to_db_dag",
    default_args={
        "owner": "jom_ariya",
        "depends_on_past": False,
        "email": ["jom_example@gmail.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    },
    description="Weekly train models with latest data including the previous week " + \
                "and make next week's forecast",
    schedule_interval=timedelta(weeks=1),  # run weekly
    start_date=datetime.now(),
    catchup=False,
    tags=["retrain", "batch_prediction", "postgres"],
) as dag:
    
    # POST to the training service
    kafka_spark_to_db_task = BashOperator(
        task_id="call_train_service", bash_command="curl -X POST http://nginx/api/trainers/train"
    )

    # if we use Dask, need a way to keep checking when the training is done then can proceed

    # loop to create request body for the incoming week as in post_service.py

    # POST to forecast service

    # Save returned results to postgres
    ## Convert JSON to pandas
    ## Call .to_sql()