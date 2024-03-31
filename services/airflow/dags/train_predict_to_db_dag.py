import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from task_operators import (
    check_status,
    get_all_store_product,
    build_batch_request_body,
    post_forecast,
    save_forecasts_to_db,
)

TRAINING_SERVICE_SERVER = os.getenv("TRAINING_SERVICE_SERVER", "nginx")
TRAINING_SERVICE_URL_PREFIX = os.getenv("TRAINING_SERVICE_URL_PREFIX", "api/trainers/")

with DAG(
    dag_id="train_predict_to_db_dag",
    default_args={
        "owner": "jom_ariya",
        "depends_on_past": False,
        "email": ["jom_example@gmail.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(seconds=30),
    },
    description="Weekly train models with latest data including the previous week "
    + "and make next week's forecast",
    schedule_interval=timedelta(weeks=1),  # run weekly
    start_date=datetime.now(),
    catchup=False,
    tags=["retrain", "batch_prediction", "postgres"],
) as dag:

    # POST to the training service
    trigger_train_task = BashOperator(
        task_id="call_train_service",
        bash_command=f"curl -X POST http://{TRAINING_SERVICE_SERVER}/{TRAINING_SERVICE_URL_PREFIX}train",
        # bash_command=f"curl -X POST http://{TRAINING_SERVICE_SERVER}/{TRAINING_SERVICE_URL_PREFIX}100/product_A/train",
    )

    # Poll the status of the training job
    check_status_task = PythonOperator(  # Use PythonOperator for XCom interaction
        task_id="check_status",
        python_callable=check_status,
        provide_context=True,  # Access TaskInstance ('ti')
    )

    # get the table from sql then find Distinct for store_id and product_name
    get_all_store_product_task = PythonOperator(
        task_id="get_all_store_product", python_callable=get_all_store_product
    )

    # loop to create request body for the incoming week as in post_service.py
    build_request_body_task = PythonOperator(
        task_id="build_request_body",
        python_callable=build_batch_request_body,
        provide_context=True,
    )

    # POST to forecast service
    post_forecast_task = PythonOperator(
        task_id="post_forecast",
        python_callable=post_forecast,
        provide_context=True,
    )

    # Save returned results to postgres
    save_forecasts_to_db_task = PythonOperator(
        task_id="save_forecasts_to_db",
        python_callable=save_forecasts_to_db,
        provide_context=True,
    )

    (
        trigger_train_task
        >> check_status_task
        >> get_all_store_product_task
        >> build_request_body_task
        >> post_forecast_task
        >> save_forecasts_to_db_task
    )
