import os
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

SALES_TABLE_NAME = os.getenv('SALES_TABLE_NAME', 'rossman_sales')

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
    productname = Column(String)