import os
import time
import pandas as pd
import altair as alt
import requests
import streamlit as st
from collections import defaultdict
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from db_utils import (
    get_table_from_engine,
    open_db_session,
    query_store_product_last_rows,
    unique_list_from_col,
    df_from_query,
)

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


def create_begin_end_date(n_days=7):
    now = datetime.now().replace(tzinfo=None)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    next_n = today + timedelta(days=n_days)
    begin_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = (today + timedelta(days=n_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return begin_date, end_date


def build_forecast_request_body(store_id: int, product_name: str, n_days=7):
    forecast_requests = []
    begin_date, end_date = create_begin_end_date(n_days)
    forecast_request = {
        "store_id": store_id,
        "product_name": product_name,
        "begin_date": begin_date,
        "end_date": end_date,
    }
    forecast_requests.append(forecast_request)
    return forecast_requests


def wait_until_status(
    endpoint, status_to_wait_for, poll_interval=5, timeout_seconds=30
):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        resp = requests.get(endpoint)
        resp = resp.json()
        train_job_id, status = resp["train_job_id"], resp["status"]
        st.write(f"status: {status}")
        if str(status) in status_to_wait_for:
            return status
        time.sleep(poll_interval)
    return status


def line_chart_from_df(
    df: pd.DataFrame, date_col: str = "forecast_date", value_col: str = "forecast_sale"
):
    min_date = df[date_col].min().strftime("%Y-%m-%d")
    max_date = df[date_col].max().strftime("%Y-%m-%d")
    model_name = df[df["forecast_date"] == df["forecast_date"].max()][
        "model_name"
    ].item()
    model_version = df[df["forecast_date"] == df["forecast_date"].max()][
        "model_version"
    ].item()
    base = alt.Chart(
        df,
        title=alt.Title(
            f"Sales Forecast of the week {min_date} to {max_date}",
            subtitle=f"model: {model_name}  |  version: {model_version}  |  CI: 95%",
        ),
    ).encode(
        x=alt.X(f"{date_col}:T", axis=alt.Axis(title="Date")),
        y=alt.Y(f"{value_col}:Q", axis=alt.Axis(title="Sales forecast")),
    )

    line = base.mark_line(color="steelblue").encode(
        tooltip=[date_col, value_col]  # Add tooltip for date and value
    )
    points = base.mark_circle(color="steelblue").encode(opacity=alt.value(0.8))
    area = base.mark_area(color="steelblue", opacity=0.3).encode(
        y="lower_ci", y2="upper_ci"
    )
    chart = (
        (area + line + points).properties(width=600, height=400).interactive()
    )  # Combine line and points

    chart = (
        chart.configure_title(
            fontSize=20,
            font="Arial",
            color="navy",  # Customize title font size, style, and color
            subtitleFontSize=15,  # Set the font size for the subtitle
            subtitleFont="Arial",  # Set the font style for the subtitle
            subtitleColor="gray",  # Set the color for the subtitle
        )
        .configure_axis(
            labelFontSize=12,
            titleFontSize=14,
            titleFont="Arial",
            titleColor="gray",  # Customize axis label and title font properties
        )
        .configure_view(strokeWidth=0)  # Remove chart border
        .configure_legend(
            title=None,
            labelFontSize=12,
            labelFont="Arial",
            labelColor="steelblue",  # Customize legend font properties
        )
    )

    return chart


def get_all_store_product():
    engine = create_engine(DB_CONNECTION_URL)
    table = get_table_from_engine(engine, SALES_TABLE_NAME)
    session = open_db_session(engine)
    store_ids = unique_list_from_col(session, table, column="store")
    product_names = unique_list_from_col(session, table, column="productname")
    return {"store": store_ids, "productname": product_names}


def df_from_forecast_response(forecast_results):
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
    return forecast_df
