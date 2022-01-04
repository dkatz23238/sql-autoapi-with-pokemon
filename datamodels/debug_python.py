import pymysql

pymysql.install_as_MySQLdb()

# Automatic Rest API from SQLAlchemy DataModels
from typing import Optional, List, Tuple
import inspect

from fastapi import FastAPI, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from sqlalchemy import create_engine, exc, insert
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
import uvicorn
import os
import jwt
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.sql import text

from sqlalchemy import Column, String, Integer
from datamodels.models import Pokemon

class DoesNotExist(Exception):
    pass


class BadQQuery(Exception):
    pass


class Forbidden(Exception):
    pass


JWT_SECRET = "BABOONS_ARE_NOT_GIBBONS"


conn_string = os.environ.get("DB_CONN_STRING")
engine = create_engine(conn_string)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

pokemon = db.query(Pokemon).all()

for p in pokemon:
    print(p.id)