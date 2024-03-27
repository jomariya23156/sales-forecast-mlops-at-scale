import os
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from db_tables import Base, RossmanSalesTable

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

SALES_TABLE_NAME = os.getenv('SALES_TABLE_NAME', 'rossman_sales')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_CONNECTION_URL = os.getenv('DB_CONNECTION_URL', f'postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db')

def subtract_date(baseline_date, this_date):
    base = datetime.strptime(baseline_date, '%Y-%m-%d')
    current = datetime.strptime(this_date, '%Y-%m-%d')
    return (base - current).days

def date_from_baseline_back(baseline, n_days):
    return (baseline - timedelta(days=n_days)).strftime('%Y-%m-%d')

logging.info('Reading data from csv...')
df = pd.read_csv('datasets/rossmann-store-sales/train_exclude_last_10d.csv')
ori_cols_order = df.columns

logging.info('Processing data...')
# get today with only Y-m-d
now = datetime.now()
today = now.replace(hour=0, minute=0, second=0, microsecond=0)
yesterday = today - timedelta(days=1)

# get latest 5 months data
df['Month'] = df['Date'].apply(lambda x: x[:x.rfind('-')])
df_sort = df.sort_values('Date', ascending=True)
last_months = df_sort['Month'].unique()[-5:]
last_months_df = df_sort[df_sort['Month'].isin(last_months)]

# convert to relative to time.now()
latest_day = last_months_df.iloc[-1]['Date']
last_months_df['days_from_latest'] = last_months_df['Date'].apply(lambda x: subtract_date(latest_day, x))
last_months_df['Relative date'] = last_months_df['days_from_latest'].apply(lambda x: date_from_baseline_back(yesterday, x))

# clean up
last_months_df = last_months_df.drop(['Date', 'days_from_latest', 'Month'], axis=1)
last_months_df = last_months_df.rename(columns={'Relative date': 'Date'})

# add a dummy item name as an example for extensibility
last_months_df['ProductName'] = "product_A"
# rearrange columns
last_months_df = last_months_df[list(ori_cols_order)+["ProductName"]]
last_months_df.columns = map(lambda x: x.lower(), last_months_df.columns)

# NOTE: We are not fucusing on model performance in this project, and of course, this time conversion 
# hurts the performance because it will mess up the holidays data (sales on holidays)
# time conversion is here for mimick the realistic usage scenario only

logging.info('Connecting to database...')
engine = create_engine(DB_CONNECTION_URL)
# drop if exsist and create table
if engine.has_table(RossmanSalesTable.__tablename__):
    Base.metadata.drop_all(engine, tables=[RossmanSalesTable.__table__])
engine = create_engine(DB_CONNECTION_URL)
Base.metadata.create_all(engine)

logging.info('Inserting dataframe to database...')
start = time.time()
# Create a brand new empty table before if_exists='append' is important
# otherwise, the table will be created with the wrong schema
last_months_df.to_sql(SALES_TABLE_NAME, engine, if_exists='append', index=False)
logging.info(f'Putting df to postgres took {time.time()-start:.3f} s')