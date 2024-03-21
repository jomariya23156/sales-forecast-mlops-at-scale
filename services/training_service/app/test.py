import os
from db_utils import get_latest_df_from_db

SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_CONNECTION_URL = os.getenv(
    "DB_CONNECTION_URL",
    f"postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db",
)

df = get_latest_df_from_db(
    DB_CONNECTION_URL, SALES_TABLE_NAME, date_col="date", last_days=(4 * 30)
)

df.to_csv("test_latest_4m.csv", index=False)
