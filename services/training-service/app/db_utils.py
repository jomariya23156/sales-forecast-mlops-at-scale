import sqlalchemy
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base


def get_table_from_engine(engine, table_name):
    Base = automap_base()
    Base.prepare(autoload_with=engine)
    table_obj = getattr(Base.classes, table_name)
    return table_obj


def open_db_session(engine: sqlalchemy.engine) -> sqlalchemy.orm.Session:
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def query_last_rows(session, table, date_col="date", last_days=None, last_n=None):
    q = session.query(table)
    table_date = getattr(table, date_col)
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


def get_latest_df_from_db(
    db_con_url: str, table_name: str, date_col: str = "date", last_days: int = (4 * 30)
) -> pd.DataFrame:
    engine = create_engine(db_con_url)
    session = open_db_session(engine)
    table_obj = get_table_from_engine(engine, table_name)
    ret = query_last_rows(session, table_obj, date_col=date_col, last_days=last_days)
    all_cols = [column.name for column in table_obj.__table__.columns]
    df = df_from_query(ret, all_cols)
    return df
