import os
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import create_engine
from db_utils import (
    open_db_session,
    unique_list_from_col,
    get_table_from_engine,
    prepare_db,
)

TRAINING_SERVICE_SERVER = os.getenv("TRAINING_SERVICE_SERVER", "nginx")
TRAINING_SERVICE_URL_PREFIX = os.getenv("TRAINING_SERVICE_URL_PREFIX", "api/trainers/")
FORECAST_ENDPOINT_URL = os.getenv(
    "FORECAST_ENDPOINT_URL", f"http://nginx/api/forecasters/forecast"
)
SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
FORECAST_TABLE_NAME = os.getenv("FORECAST_TABLE_NAME", "forecast_results")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_CONNECTION_URL = os.getenv(
    "DB_CONNECTION_URL",
    f"postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db",
)


def get_all_store_product():
    engine = create_engine(DB_CONNECTION_URL)
    table = get_table_from_engine(engine, SALES_TABLE_NAME)
    session = open_db_session(engine)
    store_ids = unique_list_from_col(session, table, column="store")
    product_names = unique_list_from_col(session, table, column="productname")
    return {"store": store_ids, "productname": product_names}


def wait_until_status(
    endpoint, status_to_wait_for, poll_interval=5, timeout_seconds=30
):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        resp = requests.get(endpoint)
        resp = resp.json()
        train_job_id, status = resp["train_job_id"], resp["status"]
        print(f"status: {status}")
        if str(status) in status_to_wait_for:
            break
        time.sleep(poll_interval)


def check_status(**kwargs):  # New function for task
    ti = kwargs["ti"]
    resp_str = ti.xcom_pull(task_ids="call_train_service")  # Pull XCom
    resp_json = json.loads(resp_str)
    print(f"resp_json: {resp_json} | type: {type(resp_json)}")
    print("Watching training task status...")
    status_to_wait_for = {"SUCCEEDED", "STOPPED", "FAILED"}
    wait_until_status(
        endpoint=f"http://{TRAINING_SERVICE_SERVER}/{TRAINING_SERVICE_URL_PREFIX}training_job_status/{resp_json['train_job_id']}",
        status_to_wait_for=status_to_wait_for,
        poll_interval=5,
        timeout_seconds=60 * 30,
    )


def create_begin_end_date(n_days=7):
    now = datetime.now().replace(tzinfo=None)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    next_n = today + timedelta(days=n_days)
    begin_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = (today + timedelta(days=n_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return begin_date, end_date


def build_batch_request_body(**kwargs):  # New function for task
    ti = kwargs["ti"]
    store_product_dict = ti.xcom_pull(task_ids="get_all_store_product")  # Pull XCom
    print(f"type: {type(store_product_dict)}")
    store_ids, product_names = (
        store_product_dict["store"],
        store_product_dict["productname"],
    )
    forecast_requests = []
    begin_date, end_date = create_begin_end_date(n_days=7)
    for store_id in store_ids:
        for product_name in product_names:
            forecast_request = {
                "store_id": store_id,
                "product_name": product_name,
                "begin_date": begin_date,
                "end_date": end_date,
            }
            forecast_requests.append(forecast_request)
    return forecast_requests


def post_forecast(**kwargs):  # New function for task
    ti = kwargs["ti"]
    requst_body = ti.xcom_pull(task_ids="build_request_body")  # Pull XCom
    print(f"type: {type(requst_body)}")
    resp = requests.post(FORECAST_ENDPOINT_URL, json=requst_body)
    print(f"Status: {resp.status_code}")
    return resp.json()


def save_forecasts_to_db(**kwargs):  # New function for task
    ti = kwargs["ti"]
    forecast_results = ti.xcom_pull(task_ids="post_forecast")  # Pull XCom
    print(f"type: {type(forecast_results)}")
    # prepare db (create if not exists) a new table named forecast_results
    prepare_db()
    engine = create_engine(DB_CONNECTION_URL)
    data = defaultdict(list)
    for result in forecast_results:
        forecasts = result["forecast"]
        request = result["request"]
        api = result["api"]
        for forecast in forecasts:
            forecast_date = datetime.strptime(
                forecast["timestamp"], "%Y-%m-%dT%H:%M:%S"
            )
            data["store"].append(request["store_id"])
            data["productname"].append(request["product_name"])
            data["forecast_date"].append(forecast_date)
            data["forecast_sale"].append(forecast["value"])
            data["lower_ci"].append(forecast["lower_ci"])
            data["upper_ci"].append(forecast["upper_ci"])
            data["model_name"].append(api["model_name"])
            data["model_version"].append(api["model_version"])
            data["created_on"].append(datetime.now())
    forecast_df = pd.DataFrame(data)
    forecast_df.to_sql(FORECAST_TABLE_NAME, engine, if_exists="append", index=False)
    print(f"Finished putting data into table {FORECAST_TABLE_NAME}")
