from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from datetime import date, datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import null
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Date


from datamodels.models import (
    Base,
)

from datamodels.user_models import Base as UserBase
from datamodels.interactable_views import Base as ViewBase

if __name__ == "__main__":
    # connection
    engine = create_engine("mysql://playground:playground@127.0.0.1:3306/playground")

    # create metadata
    Base.metadata.create_all(engine)
    UserBase.metadata.create_all(engine)
    ViewBase.metadata.create_all(engine)
