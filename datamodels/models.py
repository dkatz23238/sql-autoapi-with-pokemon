from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
    CheckConstraint,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.selectable import FromGrouping
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy import Index
from sqlalchemy import event

Base = declarative_base()


class Pokemon(Base):
    __tablename__ = "pokemon"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    weight = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

class Type(Base):
    __tablename__ = "type"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)


class Move(Base):
    __tablename__ = "move"
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("type.id"))
    name = Column(String(255), nullable=False, unique=True)
    damage = Column(Integer, nullable=False)
    

class PokemonMove(Base):
    __tablename__ = "pokemon_move"
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey('pokemon.id'))
    move_id = Column(Integer, ForeignKey("move.id"))
    __tableargs__ = (
          UniqueConstraint('pokemon_id', 'move_id', name='uix_1')
    )
    
@event.listens_for(Pokemon, "before_insert")
def pokemon_before_insert(mapper, connection, target):
    pass

@event.listens_for(Pokemon, "after_insert")
def pokemon_after_insert(mapper, connection, target):
    pass