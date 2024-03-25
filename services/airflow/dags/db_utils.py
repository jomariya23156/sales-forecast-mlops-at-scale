import os
import sqlalchemy
from datetime import datetime
from typing import List, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.automap import automap_base

SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
FORECAST_TABLE_NAME = os.getenv("FORECAST_TABLE_NAME", "forecast_results")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_CONNECTION_URL = os.getenv(
    "DB_CONNECTION_URL",
    f"postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db",
)

Base = declarative_base()


class ForecastResultsTable(Base):
    __tablename__ = FORECAST_TABLE_NAME
    id = Column(Integer, primary_key=True)
    store = Column(Integer)
    productname = Column(String)
    forecast_date = Column(DateTime)
    forecast_sale = Column(Integer)
    lower_ci = Column(Integer)
    upper_ci = Column(Integer)
    model_name = Column(String)
    model_version = Column(String)
    created_on = Column(DateTime, default=datetime.now)


class RossmanSalesTable(Base):
    __tablename__ = SALES_TABLE_NAME
    id = Column(Integer, primary_key=True)
    store = Column(Integer)
    dayofweek = Column(Integer)
    date = Column(DateTime)
    sales = Column(Integer)
    customers = Column(Integer)
    open = Column(Integer)
    promo = Column(Integer)
    stateholiday = Column(String)
    schoolholiday = Column(String)
    productname = Column(String)


def prepare_db() -> None:
    print("Preparing database tables...")
    engine = create_engine(DB_CONNECTION_URL)
    Base.metadata.create_all(engine)
    print("Done database preparation")


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


def get_table_from_engine(engine, table_name):
    Base = automap_base()
    Base.prepare(autoload_with=engine)
    table_obj = getattr(Base.classes, table_name)
    return table_obj
