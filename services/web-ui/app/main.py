import os
import streamlit as st
import requests
from sqlalchemy import create_engine
from db_utils import (
    get_table_from_engine,
    open_db_session,
    query_store_product_last_rows,
    unique_list_from_col,
    df_from_query,
)
from common_utils import (
    build_forecast_request_body,
    wait_until_status,
    line_chart_from_df,
    get_all_store_product,
    df_from_forecast_response,
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

if __name__ == "__main__":

    st.session_state["valid_store_id"] = True
    st.session_state["valid_product_name"] = True

    if "uniq_store_product" not in st.session_state:
        st.session_state["uniq_store_product"] = get_all_store_product()
    uniq_store_ids = st.session_state["uniq_store_product"]["store"]
    uniq_product_names = st.session_state["uniq_store_product"]["productname"]

    st.title("Project: sales-forecast-mlops-at-scale")

    # Create columns for side-by-side layout
    col1, col2 = st.columns(2)
    with col1:
        input_store_id = st.text_input("Store ID:", "")
    with col2:
        input_product_name = st.text_input("Product name:", "product_A")

    if input_store_id:
        try:
            input_store_id = int(input_store_id)
            # If the conversion succeeds, you have a valid integer store ID
            if input_store_id not in uniq_store_ids:
                st.session_state["valid_store_id"] = False
                st.error("This store id does not exist in the system.")
        except ValueError:
            st.session_state["valid_store_id"] = False
            st.error("Store ID must be an integer")
    else:
        st.session_state["valid_store_id"] = False

    if input_product_name not in uniq_product_names:
        st.session_state["valid_product_name"] = False
        st.error("This product name does not exist in the system.")

    if st.session_state["valid_store_id"] and st.session_state["valid_product_name"]:
        # query last 7-day predictions from db
        engine = create_engine(DB_CONNECTION_URL)
        forecast_table = get_table_from_engine(engine, FORECAST_TABLE_NAME)
        session = open_db_session(engine)
        # here we assume that for 1 store, 1 product. only one row/entry
        # is produced per day -> meaning last_n = last n day
        # there is last_days param in this func but it'based on the current
        # date of running, you can use that if it's what you need
        ret = query_store_product_last_rows(
            session=session,
            table=forecast_table,
            store_id=input_store_id,
            product_name=input_product_name,
            date_col="forecast_date",
            last_n=7,
        )
        all_cols = [column.name for column in forecast_table.__table__.columns]
        ret_df = df_from_query(ret, all_cols).sort_values("forecast_date")
        session.close()

        st.divider()
        chart = line_chart_from_df(
            ret_df, date_col="forecast_date", value_col="forecast_sale"
        )
        st.altair_chart(chart, use_container_width=True)

        ### Retraining ###
        st.write("Retrain a model with the lastest data possible")
        if st.button("Retrain"):
            with st.status("Retraining..", expanded=True) as status:
                st.write("POSTing to the training service...")
                st.write(
                    f"Store ID: {input_store_id} | Product name: {input_product_name}"
                )
                resp = requests.post(
                    f"http://{TRAINING_SERVICE_SERVER}/{TRAINING_SERVICE_URL_PREFIX}{input_store_id}/{input_product_name}/train"
                )
                resp_json = resp.json()
                st.json(resp_json)
                st.write("Watching training task status...")
                status_to_wait_for = {"SUCCEEDED", "STOPPED", "FAILED"}
                exit_status = wait_until_status(
                    endpoint=f"http://{TRAINING_SERVICE_SERVER}/{TRAINING_SERVICE_URL_PREFIX}training_job_status/{resp_json['train_job_id']}",
                    status_to_wait_for=status_to_wait_for,
                    poll_interval=1,
                    timeout_seconds=30,  # 30 seconds
                )
                st.write(f"Training done with status: {exit_status}")
                status.update(
                    label="Retraining completed!", state="complete", expanded=False
                )
            if exit_status == "SUCCEEDED":
                st.balloons()

        st.divider()

        ### Forecasting ###
        st.write("Make a forecast for the next days using the latest model")
        n_days = st.number_input("Number of next days to forecast", min_value=1)
        if st.button("Forecast") and n_days:
            with st.status("Forecasting..", expanded=True) as status:
                req_body = build_forecast_request_body(
                    input_store_id, input_product_name, n_days
                )
                st.write("POSTing to the forecast service...")
                resp = requests.post(FORECAST_ENDPOINT_URL, json=req_body)
                st.success("Success posting to the forecast service")
                st.json(resp.json())
                status.update(
                    label="Forecasting completed!", state="complete", expanded=False
                )
            forecast_df = df_from_forecast_response(resp.json()).sort_values(
                "forecast_date"
            )
            chart2 = line_chart_from_df(
                forecast_df, date_col="forecast_date", value_col="forecast_sale"
            )
            st.altair_chart(chart2, use_container_width=True)
