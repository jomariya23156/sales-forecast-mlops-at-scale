import os
import streamlit as st
import numpy as np
import pandas as pd
import requests

FORECAST_SERVICE_PORT = os.getenv("FORECAST_SERVICE_PORT", "4242")
FORECAST_ENDPOINT_URI = os.getenv(
    "FORECAST_ENDPOINT_URI", f"http://nginx/api/forecasters/forecast"
)

# for printing message to terminal https://discuss.streamlit.io/t/printing-in-the-terminal-but-not-the-the-sreamlit-app/53426/2
if __name__ == "__main__":
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])

    st.title("Project: sales-forecast-mlops-at-scale")
    st.line_chart(chart_data)
    if st.button("forecast"):

        # temp mock up
        body = [
            {
                "store_id": "4",
                "begin_date": "2023-03-01T00:00:00Z",
                "end_date": "2023-03-07T00:00:00Z",
            },
            {
                "store_id": "3",
                "begin_date": "2023-03-01T00:00:00Z",
                "end_date": "2023-03-07T00:00:00Z",
            },
            {
                "store_id": "10",
                "begin_date": "2023-03-01T00:00:00Z",
                "end_date": "2023-03-07T00:00:00Z",
            },
        ]
        st.write("Posting to", FORECAST_ENDPOINT_URI)
        resp = requests.post(FORECAST_ENDPOINT_URI, json=body)
        st.json(resp.json())
        st.write("Success posting")
