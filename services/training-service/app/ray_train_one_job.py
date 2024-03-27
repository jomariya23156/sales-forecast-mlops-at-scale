import os
import ray
import time
import logging
from argparse import ArgumentParser
from db_utils import get_latest_df_from_db
from train_utils import prep_train_predict

SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_CONNECTION_URL = os.getenv(
    "DB_CONNECTION_URL",
    f"postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db",
)

parser = ArgumentParser()
parser.add_argument("--store_id", type=int, default=1, help="ID of the store")
parser.add_argument(
    "--product_name", type=str, default="product_A", help="Name of the product"
)
args = vars(parser.parse_args())
store_id, product_name = args["store_id"], args["product_name"]

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

ray.init()

train_task_id = "train_" + str(time.time())
# retrieve latest 4 months data from db
logging.info("Retrieving 4 months data from db...")
df = get_latest_df_from_db(
    DB_CONNECTION_URL, SALES_TABLE_NAME, date_col="date", last_days=(4 * 30)
)
logging.info(f"Retrieved data: {len(df)} rows")

if (
    store_id not in df["store"].tolist()
    or product_name not in df["productname"].tolist()
):
    raise Exception("store_id or product_name is not existed in the system.")

# define params for modelling
seasonality = {"yearly": True, "weekly": True, "daily": False}
df_id = ray.put(df)
logging.info("Done putting DF")

train_obj_ref, metrics_obj_ref = prep_train_predict.remote(
    df_id, store_id, product_name, seasonality=seasonality
)

logging.info(f"Submitted model training for store {store_id} | product {product_name}")

results = {
    "train_data": ray.get(train_obj_ref),
    "metrics": ray.get(metrics_obj_ref),
}
