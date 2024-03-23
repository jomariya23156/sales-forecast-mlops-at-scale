import os
import ray
import logging
import mlflow
import prophet
from prophet import Prophet
import pandas as pd
from typing import List, Tuple, Dict
from sklearn.model_selection import TimeSeriesSplit
from collections import defaultdict
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    median_absolute_error,
)

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5050")


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


def calculate_metrics(df_true, df_pred):
    metrics = {
        "rmse": mean_squared_error(
            y_true=df_true["y"], y_pred=df_pred["yhat"], squared=False
        ),
        "mean_abs_perc_error": mean_absolute_percentage_error(
            y_true=df_true["y"], y_pred=df_pred["yhat"]
        ),
        "mean_abs_error": mean_absolute_error(
            y_true=df_true["y"], y_pred=df_pred["yhat"]
        ),
        "median_abs_error": median_absolute_error(
            y_true=df_true["y"], y_pred=df_pred["yhat"]
        ),
    }
    return metrics


def prep_store_data(
    df: pd.DataFrame,
    store_id: int = 4,
    product_name: str = "product_A",
    store_open: int = 1,
) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df.rename(columns={"date": "ds", "sales": "y"}, inplace=True)
    df_store = df[
        (df["store"] == store_id)
        & (df["productname"] == product_name)
        & (df["open"] == store_open)
    ].reset_index(drop=True)
    return df_store.sort_values("ds", ascending=True)


@ray.remote(num_returns=2)
def prep_train_predict(
    df: pd.DataFrame,
    store_id: int,
    product_name: str,
    store_open: int = 1,
    seasonality: dict = {"yearly": True, "weekly": True, "daily": False},
) -> Tuple[pd.DataFrame, Dict[str, float]]:

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow_client = mlflow.MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    # redis_ray = redis.Redis(host='redis', port=int(REDIS_PORT), db=1)
    with mlflow.start_run():
        logging.info("Started MLflow run")
        store_product_df = prep_store_data(
            df, store_id=store_id, product_name=product_name, store_open=store_open
        )
        logging.info(
            f"Retrieved data for store {store_id} product {product_name}: {len(store_product_df)}"
        )
        logging.info("Preprocessed data")

        # Walk-Forward (anchored) cross validation
        logging.info("Starting Walk-forward cross-validation")
        tscv = TimeSeriesSplit(n_splits=5)
        all_metrics = defaultdict(list)

        for train_index, test_index in tscv.split(store_product_df):
            df_train, df_test = (
                store_product_df.iloc[train_index],
                store_product_df.iloc[test_index],
            )

            mlflow.autolog()
            cv_model = train_forecaster(df_train, seasonality)
            test_y_pred = cv_model.predict(df_test)
            test_metrics = calculate_metrics(df_test, test_y_pred)
            all_metrics["rmse"].append(test_metrics["rmse"])
            all_metrics["mean_abs_perc_error"].append(
                test_metrics["mean_abs_perc_error"]
            )
            all_metrics["mean_abs_error"].append(test_metrics["mean_abs_error"])
            all_metrics["median_abs_error"].append(test_metrics["median_abs_error"])

        # Calculate Averaged Metrics
        avg_metrics = {}
        for (
            metric_name,
            value_list,
        ) in all_metrics.items():  # Assuming all splits have the same metrics
            avg_metrics[metric_name] = sum(value_list) / len(value_list)
        logging.info("Finished walk-forward cross-validation")

        logging.info("Started a final model training")
        final_model = train_forecaster(store_product_df, seasonality)
        logging.info("Trained model")
        mlflow.prophet.log_model(final_model, artifact_path="model")
        logging.info("Logged model to MLflow")

        run_id = mlflow.active_run().info.run_id
        mlflow.log_params(seasonality)
        mlflow.log_metrics(avg_metrics)

    # The default path where the MLflow autologging function stores the model
    artifact_path = "model"
    model_uri = f"runs:/{run_id}/{artifact_path}"

    model_name = f"prophet-retail-forecaster-store-{store_id}-{product_name}"
    model_details = mlflow.register_model(model_uri=model_uri, name=model_name)
    logging.info("Registered model")

    # transition model to production
    mlflow_client.transition_model_version_stage(
        name=model_name,
        version=model_details.version,
        stage="production",
    )
    logging.info("Transitioned model to production stage")

    return store_product_df, avg_metrics
