import sqlalchemy
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Any
from collections import defaultdict
from sqlalchemy import func, and_
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

    # Subquery to get the latest primary key for each unique combination
    latest_subquery = (
        session.query(
            table.store,
            table.productname,
            table.forecast_date,  # Assuming you have a 'forecast_date' column
            func.max(table.id).label(
                "max_pk"
            ),  # Under assumption that higher PK (id) = newer
        )
        .group_by(table.store, table.productname, table.forecast_date)
        .subquery()
    )

    # Join with the subquery to filter for latest rows
    q = q.join(
        latest_subquery,
        and_(
            table.store == latest_subquery.c.store,
            table.productname == latest_subquery.c.productname,
            table.forecast_date == latest_subquery.c.forecast_date,
            table.id == latest_subquery.c.max_pk,
        ),
    )

    # Apply 'last_days' and 'last_n' filtering
    if last_days:
        days_ago = datetime.utcnow() - timedelta(days=last_days)
        days_ago_str = days_ago.strftime("%Y-%m-%d %H:%M:%S")
        q = q.filter(func.timezone("UTC", table_date) >= days_ago_str)

    if last_n:  # Note: last_n will now get the intended "distinct" days
        q = q.order_by(table_date.desc()).limit(last_n)

    return q.all()


def df_from_query(sql_ret, use_cols) -> pd.DataFrame:
    data = defaultdict(list)
    for row in sql_ret:
        for col in use_cols:
            data[col].append(getattr(row, col))
    df = pd.DataFrame(data).set_index("id")
    return df
