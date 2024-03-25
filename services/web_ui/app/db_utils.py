import sqlalchemy
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Any
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


def open_db_session(engine: sqlalchemy.engine) -> sqlalchemy.orm.Session:
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def unique_list_from_col(
    session: sqlalchemy.orm.Session, table, column: str
) -> List[Any]:
    unique_rets = session.query(getattr(table, column)).distinct().all()
    unique_list = [ret[0] for ret in unique_rets]
    return unique_list


def get_table_from_engine(engine: sqlalchemy.engine, table_name: str):
    Base = automap_base()
    Base.prepare(autoload_with=engine)
    table_obj = getattr(Base.classes, table_name)
    return table_obj


def query_store_product_last_rows(
    session, table, store_id, product_name, date_col="date", last_days=None, last_n=None
):
    q = session.query(table)
    table_date = getattr(table, date_col)
    q = q.filter(table.store == store_id).filter(table.productname == product_name)
    if last_days:
        days_ago = datetime.utcnow() - timedelta(days=last_days)
        days_ago_str = days_ago.strftime("%Y-%m-%d %H:%M:%S")
        # Query the rows added in the last N days regardless of database time zone
        q = q.filter(func.timezone("UTC", table_date) >= days_ago_str)
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
    df = pd.DataFrame(data).set_index("id")
    return df
