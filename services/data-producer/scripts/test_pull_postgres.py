# a script for manually test if the data insertion work correctly
import os
import pandas as pd
from collections import defaultdict
import sqlalchemy
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from db_tables import RossmanSalesTable

POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_CONNECTION_URL = os.getenv('DB_CONNECTION_URL', f'postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db')

def open_db_session(engine: sqlalchemy.engine) -> sqlalchemy.orm.Session:
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def query_last_rows(session, table, date_col='date', last_days=None, last_n=None):
    q = session.query(table)
    table_date = getattr(table, date_col)
    if last_days:
        days_ago = datetime.utcnow() - timedelta(days=last_days)
        days_ago_str = days_ago.strftime('%Y-%m-%d %H:%M:%S')
        # Query the rows added in the last 7 days regardless of database time zone
        q = q.filter(
                func.timezone('UTC', table_date) >= days_ago_str
            )
        if last_n:
            q = q.limit(last_n)
        ret = q.all()
    elif last_n:
        ret = q.order_by(table_date.desc()).limit(last_n).all()
    else:
        ret = q.order_by(table_date.desc()).all()
    return ret

def df_from_query(sql_ret, use_cols) -> pd.DataFrame:
    data = defaultdict(list)
    for row in sql_ret:
        for col in use_cols:
            data[col].append(getattr(row, col))
    df = pd.DataFrame(data).set_index('id')
    return df

engine = create_engine(DB_CONNECTION_URL)
session = open_db_session(engine)

ret = query_last_rows(session, RossmanSalesTable, last_days=(3*30))
all_cols = [column.name for column in RossmanSalesTable.__table__.columns]
ret_df = df_from_query(ret, all_cols)
ret_df = ret_df.sort_values('date')
print(ret_df.tail())
# ret_df.to_csv('dev.csv')