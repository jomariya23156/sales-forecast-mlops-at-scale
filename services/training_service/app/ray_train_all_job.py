import os
import ray
import time
import logging
from db_utils import get_latest_df_from_db
from train_utils import prep_train_predict

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_CONNECTION_URL = os.getenv(
    "DB_CONNECTION_URL",
    f"postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db",
)

ray.init()

train_task_id = "train_" + str(time.time())
# retrieve latest 4 months data from db
logging.info("Retrieving 4 months data from db...")
df = get_latest_df_from_db(
    DB_CONNECTION_URL, SALES_TABLE_NAME, date_col="date", last_days=(4 * 30)
)
logging.info(f"Retrieved data: {len(df)} rows")
# optional: convert pandas df to ray df to further parallelize
# but we need to change the preprocess functions calls too
# dataset = ray.data.from_pandas(df)

# get all unique store ids & product names
store_ids = df["store"].unique()
product_names = df["productname"].unique()

# define params for modelling
seasonality = {"yearly": True, "weekly": True, "daily": False}
df_id = ray.put(df)
logging.info("Done putting DF")

train_obj_refs, metrics_obj_refs = map(
    list,
    zip(
        *(
            [
                prep_train_predict.remote(
                    df_id, store_id, product_name, seasonality=seasonality
                )
                for store_id in store_ids
                for product_name in product_names
            ]
        )
    ),
)

logging.info(f"Submitted model training for {len(store_ids)*len(product_names)} models")

train_objs = ray.get(train_obj_refs)
