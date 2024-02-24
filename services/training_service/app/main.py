import os
import ray
import time
import logging
import numpy as np
import pandas as pd
import prophet
from prophet import Prophet
import kaggle
import mlflow
from plot_utils import plot_forecast, plot_store_data
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    median_absolute_error,
)

from fastapi import FastAPI, Request

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5050")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = mlflow.MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

app = FastAPI()

def download_kaggle_dataset(
    kaggle_dataset: str = "pratyushakar/rossmann-store-sales", out_path: str = "./"
) -> None:
    kaggle.api.dataset_download_files(
        kaggle_dataset, path=out_path, unzip=True, quiet=False
    )


def prep_store_data(
    df: pd.DataFrame, store_id: int = 4, store_open: int = 1
) -> pd.DataFrame:
    df["Date"] = pd.to_datetime(df["Date"])
    df.rename(columns={"Date": "ds", "Sales": "y"}, inplace=True)
    df_store = df[(df["Store"] == store_id) & (df["Open"] == store_open)].reset_index(
        drop=True
    )
    return df_store.sort_values("ds", ascending=True)


def train_test_split_df(df: pd.DataFrame, train_fraction: float = 0.8):
    # split data
    train_index = int(train_fraction * df.shape[0])
    df_train = df.copy().iloc[:train_index]
    df_test = df.copy().iloc[train_index:]
    return df_train, df_test


def train_forecaster(
    df_train: pd.DataFrame, seasonality: dict
) -> prophet.forecaster.Prophet:
    # init and train a model
    model = Prophet(
        yearly_seasonality=seasonality["yearly"],
        weekly_seasonality=seasonality["weekly"],
        daily_seasonality=seasonality["daily"],
        interval_width=0.95,
    )
    model.fit(df_train)
    return model


# def train_predict(
#     df: pd.DataFrame, train_fraction: float, seasonality: dict
# ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:

#     df_train, df_test, train_index = train_test_split_df(
#         df, train_fraction=train_fraction
#     )

#     # init model
#     model = train_forecaster(df_train)
#     pred = model.predict(df_test)
#     return pred, df_train, df_test, train_index


@ray.remote(num_returns=3)
def prep_train_predict(
    df: pd.DataFrame,
    store_id: int,
    store_open: int = 1,
    train_fraction: float = 0.75,
    seasonality: dict = {"yearly": True, "weekly": True, "daily": False},
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:

    with mlflow.start_run():
        logging.info("Started MLflow run")
        df = prep_store_data(df, store_id=store_id, store_open=store_open)
        logging.info("Preprocessed data")

        logging.info("Splitting data")
        df_train, df_test = train_test_split_df(df, train_fraction=train_fraction)
        logging.info("Data split")

        mlflow.autolog()
        logging.info("Started model training")
        model = train_forecaster(df_train, seasonality)
        logging.info("Trained model")
        mlflow.prophet.log_model(model, artifact_path="model")
        logging.info("Logged model to MLflow")

        test_y_pred = model.predict(df_test)
        test_metrics = {
            "rmse": mean_squared_error(
                y_true=df_test["y"], y_pred=test_y_pred["yhat"], squared=False
            ),
            "mean_abs_perc_error": mean_absolute_percentage_error(
                y_true=df_test["y"], y_pred=test_y_pred["yhat"]
            ),
            "mean_abs_error": mean_absolute_error(
                y_true=df_test["y"], y_pred=test_y_pred["yhat"]
            ),
            "median_abs_error": median_absolute_error(
                y_true=df_test["y"], y_pred=test_y_pred["yhat"]
            ),
        }
        logging.info("Computed test metrics")

        run_id = mlflow.active_run().info.run_id
        mlflow.log_params(seasonality)
        mlflow.log_metrics(test_metrics)

    # The default path where the MLflow autologging function stores the model
    artifact_path = "model"
    model_uri = f"runs:/{run_id}/{artifact_path}"

    model_name = f"prophet-retail-forecaster-store-{store_id}"
    model_details = mlflow.register_model(model_uri=model_uri, name=model_name)
    logging.info("Registered model")

    # transition model to production
    client.transition_model_version_stage(
        name=model_name,
        version=model_details.version,
        stage="production",
    )
    logging.info("Transitioned model to production stage")

    return test_y_pred, df_train, df_test


@app.post('/train', status_code=200)
def train(request: Request):
    # If data present, read it in, otherwise, download it
    file_path = "./train.csv"
    if os.path.exists(file_path):
        logging.info("Dataset found, reading into pandas dataframe.")
        df = pd.read_csv(file_path)
    else:
        logging.info("Dataset not found, downloading ...")
        download_kaggle_dataset()
        logging.info("Reading dataset into pandas dataframe.")
        df = pd.read_csv(file_path)

    # optional: convert pandas df to ray df to further parallelize
    # but we need to change the preprocess functions calls too
    # dataset = ray.data.from_pandas(df)

    # get all unique store ids
    store_ids = df["Store"].unique()

    # define params for modelling
    seasonality = {"yearly": True, "weekly": True, "daily": False}

    ray.init(num_cpus=4, dashboard_host="0.0.0.0")
    df_id = ray.put(df)

    start_time = time.time()

    # for store_id in store_ids:
    #     prep_train_predict.remote(df_id, store_id, seasonality=seasonality)

    pred_obj_refs, train_obj_refs, test_obj_refs = map(
        list,
        zip(
            *(
                [
                    prep_train_predict.remote(df_id, store_id, seasonality=seasonality)
                    for store_id in store_ids
                ]
            )
        ),
    )
    # in fact we don't really need to return objects and .get() in this case
    # cuz everything we want saved to MLflow. but since we don't have a Ray cluster setup
    # it will be created and shutdown on the execution of this script and if we don't
    # call .get() ray won't wait til the tasks are done it will just submit the task
    # to the cluster and return ref objs immediately
    results = {
        "predictions": ray.get(pred_obj_refs),
        "train_data": ray.get(train_obj_refs),
        "test_data": ray.get(test_obj_refs),
    }
    train_time = time.time() - start_time

    ray.shutdown()
    logging.info(f"Models trained {len(store_ids)}")
    logging.info(f"Took {train_time:.4f} seconds")
    return {"message": "Successfully trained models", "n_trained_models": len(store_ids)}