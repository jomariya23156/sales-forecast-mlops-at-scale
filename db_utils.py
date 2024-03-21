import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

SALES_TABLE_NAME = os.getenv("SALES_TABLE_NAME", "rossman_sales")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_CONNECTION_URL = os.getenv(
    "DB_CONNECTION_URL",
    f"postgresql://spark_user:SuperSecurePwdHere@postgres:{POSTGRES_PORT}/spark_pg_db",
)

Base = declarative_base()


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


def prepare_db() -> None:
    print("Preparing database tables...")
    engine = create_engine(DB_CONNECTION_URL)
    Base.metadata.create_all(engine)
    print("Done database preparation")
