from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.selectable import FromGrouping
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy import Index

Base = declarative_base()


class AvailableSQLViews(Base):
    __tablename__ = "available_sql_views"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
