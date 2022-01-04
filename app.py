# /usr/bin/python
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


class DoesNotExist(Exception):
    pass


class BadQQuery(Exception):
    pass


class Forbidden(Exception):
    pass


JWT_SECRET = "BABOONS_ARE_NOT_GIBBONS"

app = FastAPI()
conn_string = os.environ.get("DB_CONN_STRING")
engine = create_engine(conn_string)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_default_origins = "http://localhost,http://localhost:8080"

origins = os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def marshall_dict(d: dict) -> dict:
    _d = {}
    for key in d:
        if isinstance(d, datetime.datetime):
            _d[key] = d[key].isoformat()
        elif isinstance(d, int) or isinstance(d, float) or isinstance(d, str):
            _d[key] = d[key]
    return d


def inspct_mbmrs(t: object) -> List[Tuple[str, str]]:
    return [[str(i), str(j)] for i, j in inspect.getmembers(t)]


def parse_query(q: str) -> dict:
    if ":" not in q:
        raise BadQQuery()

    split = q.split(":")

    if len(split) != 2:
        raise BadQQuery()

    k = split[0]
    v = split[1]

    try:
        v = int(v)
    except:
        pass

    return {k: v}


# Dependency Injections
def get_db() -> SessionLocal:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


### User and Authentication Services

from datamodels.user_models import User
from datamodels.interactable_views import AvailableSQLViews


class UserPostModel(BaseModel):
    username: str
    password: str


class UserGetModel(BaseModel):
    id: int
    username: str


def create_user_with_session(db: Session, user: UserPostModel) -> int:
    user_dict = user.dict()
    user_dict["password"] = "ENCRYPTED____" + user_dict["password"]
    stmt = insert(User).values(**user_dict)
    r = db.execute(stmt)
    db.commit()
    _id = r.inserted_primary_key["id"]
    return {"id": _id}


def authenticate_user_with_session(db: Session, user: UserPostModel):
    user_dict = user.dict()
    uname = user_dict["username"]
    user_dict["password"] = "ENCRYPTED____" + user_dict["password"]
    queried_user = db.query(User).filter_by(**{"username": uname}).first()
    if queried_user is None:
        raise DoesNotExist(f"{uname} does not exist")

    if queried_user.password != user_dict["password"]:
        raise Forbidden()

    encoded_jwt = jwt.encode({"sub": queried_user.id}, "secret", algorithm="HS256")
    return {"token": encoded_jwt}


class UserSignUpOut(BaseModel):
    id: int


class AuthOut(BaseModel):
    token: str


@app.post(
    "/users/signup",
    response_model=UserSignUpOut,
    operation_id="user_sign_up_out",
    tags=["Users"],
)
async def sign_up_user(new_user: UserPostModel, db: Session = Depends(get_db)):
    try:
        return create_user_with_session(db, new_user)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


@app.post(
    "/users/authenticate",
    response_model=AuthOut,
    operation_id="authenticate",
    tags=["Users"],
)
async def authenticate_user(user: UserPostModel, db: Session = Depends(get_db)):
    try:
        return authenticate_user_with_session(db, user)
    except DoesNotExist as e:
        db.rollback()
        return JSONResponse(
            status_code=404, content={"succes": False, "error": "not found"}
        )
    except Forbidden as e:
        db.rollback()
        return JSONResponse(
            status_code=403, content={"sucuess": False, "error": "You can't do that."}
        )


def get_available_views_with_session(db):
    rows = db.query(AvailableSQLViews).all()
    _rows = []
    for r in rows:
        _rows.append(str(r.name))
    return _rows


### Model Services

from datamodels.models import Move

# Data Models
class MovePostModel(BaseModel):

    type_id: int

    name: str

    damage: int


class MovePutModel(BaseModel):

    type_id: Optional[int]

    name: Optional[str]

    damage: Optional[int]


class MoveGetSingleModel(BaseModel):

    id: int

    type_id: Optional[int]

    name: str

    damage: int


class MoveGetManyModel(BaseModel):
    moves: List[MoveGetSingleModel]


## Service functions for Move
def get_move_with_session(
    db: Session, skip: int = 0, limit: int = 100, q: Optional[str] = None
) -> List[dict]:
    if q:
        try:
            q = parse_query(q)
            items = db.query(Move).filter_by(**q).offset(skip).limit(limit).all()
            items = [marshall_dict(d.__dict__) for d in items]
        except BadQQuery:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! Format must follow 'key:value'."
                },
            )
        except exc.InvalidRequestError:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! key must contain valid columns"
                },
            )

    else:
        items = db.query(Move).offset(skip).limit(limit).all()
        items = [marshall_dict(d.__dict__) for d in items]
    return items


def get_single_move_with_session(db: Session, move_id) -> Optional[dict]:
    item = db.query(Move).filter(Move.id == move_id).first()
    if item is not None:
        return marshall_dict(item.__dict__)
    else:
        return None


def create_move_with_session(db: Session, move: MovePostModel) -> int:
    new_move = Move(**move.dict())
    db.add(new_move)
    # print((str(stmt)))
    # r = db.execute(stmt)
    db.commit()
    return new_move.id


def update_move_with_session(db: Session, move_id: int, move: MovePutModel) -> dict:
    update_dict = {k: v for k, v in move.dict().items() if v is not None}
    item_to_update = db.query(Move).filter(Move.id == move_id).update(update_dict)
    db.commit()
    return {"success": True}


def delete_move_with_session(db: Session, move_id: int) -> dict:
    el = db.query(Move).filter(Move.id == move_id).first()
    if el is not None:
        db.query(Move).filter_by(id=move_id).delete()
        db.commit()
        return {"success": True}
    else:
        raise DoesNotExist()


### APP ROUTES FOR Move
# Get Single
@app.get(
    "/move/{move_id}",
    response_model=MoveGetSingleModel,
    operation_id="get_single_move",
    tags=["Move"],
)
async def get_single_move(move_id: int, db: Session = Depends(get_db)):
    _item = get_single_move_with_session(db, move_id)
    if _item:
        return _item
    else:
        return JSONResponse(status_code=404, content={"message": "Not Found"})


# Get Many Resources
@app.get(
    "/move",
    response_model=List[MoveGetSingleModel],
    operation_id="get_many_move",
    tags=["Move"],
)
async def get_many_move(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
):
    return get_move_with_session(db, q=q)


# Create A Unique Resource
@app.post("/move", operation_id="create_single_move", tags=["Move"])
async def post_move(new_move: MovePostModel, db: Session = Depends(get_db)):
    try:
        return create_move_with_session(db, new_move)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Update A Unique Resource
@app.put("/move/{move_id}", operation_id="edit_single_move", tags=["Move"])
async def put_move(move_id: int, move: MovePutModel, db: Session = Depends(get_db)):
    try:
        return update_move_with_session(db, move_id, move)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Delete A Unique Resource
@app.delete("/move/{move_id}", operation_id="delete_single_move", tags=["Move"])
async def delete_move(move_id: int, db: Session = Depends(get_db)):
    try:
        return delete_move_with_session(db, move_id)
    except DoesNotExist:
        return JSONResponse(
            status_code=404,
            content={"message": "move does not exist with id == " + str(move_id)},
        )
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


from datamodels.models import Pokemon

# Data Models
class PokemonPostModel(BaseModel):

    name: str

    weight: int

    height: int


class PokemonPutModel(BaseModel):

    name: Optional[str]

    weight: Optional[int]

    height: Optional[int]


class PokemonGetSingleModel(BaseModel):

    id: int

    name: str

    weight: int

    height: int


class PokemonGetManyModel(BaseModel):
    pokemons: List[PokemonGetSingleModel]


## Service functions for Pokemon
def get_pokemon_with_session(
    db: Session, skip: int = 0, limit: int = 100, q: Optional[str] = None
) -> List[dict]:
    if q:
        try:
            q = parse_query(q)
            items = db.query(Pokemon).filter_by(**q).offset(skip).limit(limit).all()
            items = [marshall_dict(d.__dict__) for d in items]
        except BadQQuery:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! Format must follow 'key:value'."
                },
            )
        except exc.InvalidRequestError:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! key must contain valid columns"
                },
            )

    else:
        items = db.query(Pokemon).offset(skip).limit(limit).all()
        items = [marshall_dict(d.__dict__) for d in items]
    return items


def get_single_pokemon_with_session(db: Session, pokemon_id) -> Optional[dict]:
    item = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if item is not None:
        return marshall_dict(item.__dict__)
    else:
        return None


def create_pokemon_with_session(db: Session, pokemon: PokemonPostModel) -> int:
    new_pokemon = Pokemon(**pokemon.dict())
    db.add(new_pokemon)
    # print((str(stmt)))
    # r = db.execute(stmt)
    db.commit()
    return new_pokemon.id


def update_pokemon_with_session(
    db: Session, pokemon_id: int, pokemon: PokemonPutModel
) -> dict:
    update_dict = {k: v for k, v in pokemon.dict().items() if v is not None}
    item_to_update = (
        db.query(Pokemon).filter(Pokemon.id == pokemon_id).update(update_dict)
    )
    db.commit()
    return {"success": True}


def delete_pokemon_with_session(db: Session, pokemon_id: int) -> dict:
    el = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if el is not None:
        db.query(Pokemon).filter_by(id=pokemon_id).delete()
        db.commit()
        return {"success": True}
    else:
        raise DoesNotExist()


### APP ROUTES FOR Pokemon
# Get Single
@app.get(
    "/pokemon/{pokemon_id}",
    response_model=PokemonGetSingleModel,
    operation_id="get_single_pokemon",
    tags=["Pokemon"],
)
async def get_single_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    _item = get_single_pokemon_with_session(db, pokemon_id)
    if _item:
        return _item
    else:
        return JSONResponse(status_code=404, content={"message": "Not Found"})


# Get Many Resources
@app.get(
    "/pokemon",
    response_model=List[PokemonGetSingleModel],
    operation_id="get_many_pokemon",
    tags=["Pokemon"],
)
async def get_many_pokemon(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
):
    return get_pokemon_with_session(db, q=q)


# Create A Unique Resource
@app.post("/pokemon", operation_id="create_single_pokemon", tags=["Pokemon"])
async def post_pokemon(new_pokemon: PokemonPostModel, db: Session = Depends(get_db)):
    try:
        return create_pokemon_with_session(db, new_pokemon)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Update A Unique Resource
@app.put("/pokemon/{pokemon_id}", operation_id="edit_single_pokemon", tags=["Pokemon"])
async def put_pokemon(
    pokemon_id: int, pokemon: PokemonPutModel, db: Session = Depends(get_db)
):
    try:
        return update_pokemon_with_session(db, pokemon_id, pokemon)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Delete A Unique Resource
@app.delete(
    "/pokemon/{pokemon_id}", operation_id="delete_single_pokemon", tags=["Pokemon"]
)
async def delete_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    try:
        return delete_pokemon_with_session(db, pokemon_id)
    except DoesNotExist:
        return JSONResponse(
            status_code=404,
            content={"message": "pokemon does not exist with id == " + str(pokemon_id)},
        )
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


from datamodels.models import PokemonMove

# Data Models
class PokemonMovePostModel(BaseModel):

    pokemon_id: int

    move_id: int


class PokemonMovePutModel(BaseModel):

    pokemon_id: Optional[int]

    move_id: Optional[int]


class PokemonMoveGetSingleModel(BaseModel):

    id: int

    pokemon_id: Optional[int]

    move_id: Optional[int]


class PokemonMoveGetManyModel(BaseModel):
    pokemon_moves: List[PokemonMoveGetSingleModel]


## Service functions for PokemonMove
def get_pokemon_move_with_session(
    db: Session, skip: int = 0, limit: int = 100, q: Optional[str] = None
) -> List[dict]:
    if q:
        try:
            q = parse_query(q)
            items = db.query(PokemonMove).filter_by(**q).offset(skip).limit(limit).all()
            items = [marshall_dict(d.__dict__) for d in items]
        except BadQQuery:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! Format must follow 'key:value'."
                },
            )
        except exc.InvalidRequestError:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! key must contain valid columns"
                },
            )

    else:
        items = db.query(PokemonMove).offset(skip).limit(limit).all()
        items = [marshall_dict(d.__dict__) for d in items]
    return items


def get_single_pokemon_move_with_session(
    db: Session, pokemon_move_id
) -> Optional[dict]:
    item = db.query(PokemonMove).filter(PokemonMove.id == pokemon_move_id).first()
    if item is not None:
        return marshall_dict(item.__dict__)
    else:
        return None


def create_pokemon_move_with_session(
    db: Session, pokemon_move: PokemonMovePostModel
) -> int:
    new_pokemon_move = PokemonMove(**pokemon_move.dict())
    db.add(new_pokemon_move)
    # print((str(stmt)))
    # r = db.execute(stmt)
    db.commit()
    return new_pokemon_move.id


def update_pokemon_move_with_session(
    db: Session, pokemon_move_id: int, pokemon_move: PokemonMovePutModel
) -> dict:
    update_dict = {k: v for k, v in pokemon_move.dict().items() if v is not None}
    item_to_update = (
        db.query(PokemonMove)
        .filter(PokemonMove.id == pokemon_move_id)
        .update(update_dict)
    )
    db.commit()
    return {"success": True}


def delete_pokemon_move_with_session(db: Session, pokemon_move_id: int) -> dict:
    el = db.query(PokemonMove).filter(PokemonMove.id == pokemon_move_id).first()
    if el is not None:
        db.query(PokemonMove).filter_by(id=pokemon_move_id).delete()
        db.commit()
        return {"success": True}
    else:
        raise DoesNotExist()


### APP ROUTES FOR PokemonMove
# Get Single
@app.get(
    "/pokemon_move/{pokemon_move_id}",
    response_model=PokemonMoveGetSingleModel,
    operation_id="get_single_pokemon_move",
    tags=["PokemonMove"],
)
async def get_single_pokemon_move(pokemon_move_id: int, db: Session = Depends(get_db)):
    _item = get_single_pokemon_move_with_session(db, pokemon_move_id)
    if _item:
        return _item
    else:
        return JSONResponse(status_code=404, content={"message": "Not Found"})


# Get Many Resources
@app.get(
    "/pokemon_move",
    response_model=List[PokemonMoveGetSingleModel],
    operation_id="get_many_pokemon_move",
    tags=["PokemonMove"],
)
async def get_many_pokemon_move(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
):
    return get_pokemon_move_with_session(db, q=q)


# Create A Unique Resource
@app.post(
    "/pokemon_move", operation_id="create_single_pokemon_move", tags=["PokemonMove"]
)
async def post_pokemon_move(
    new_pokemon_move: PokemonMovePostModel, db: Session = Depends(get_db)
):
    try:
        return create_pokemon_move_with_session(db, new_pokemon_move)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Update A Unique Resource
@app.put(
    "/pokemon_move/{pokemon_move_id}",
    operation_id="edit_single_pokemon_move",
    tags=["PokemonMove"],
)
async def put_pokemon_move(
    pokemon_move_id: int,
    pokemon_move: PokemonMovePutModel,
    db: Session = Depends(get_db),
):
    try:
        return update_pokemon_move_with_session(db, pokemon_move_id, pokemon_move)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Delete A Unique Resource
@app.delete(
    "/pokemon_move/{pokemon_move_id}",
    operation_id="delete_single_pokemon_move",
    tags=["PokemonMove"],
)
async def delete_pokemon_move(pokemon_move_id: int, db: Session = Depends(get_db)):
    try:
        return delete_pokemon_move_with_session(db, pokemon_move_id)
    except DoesNotExist:
        return JSONResponse(
            status_code=404,
            content={
                "message": "pokemon_move does not exist with id == "
                + str(pokemon_move_id)
            },
        )
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


from datamodels.models import Type

# Data Models
class TypePostModel(BaseModel):

    name: str


class TypePutModel(BaseModel):

    name: Optional[str]


class TypeGetSingleModel(BaseModel):

    id: int

    name: str


class TypeGetManyModel(BaseModel):
    types: List[TypeGetSingleModel]


## Service functions for Type
def get_type_with_session(
    db: Session, skip: int = 0, limit: int = 100, q: Optional[str] = None
) -> List[dict]:
    if q:
        try:
            q = parse_query(q)
            items = db.query(Type).filter_by(**q).offset(skip).limit(limit).all()
            items = [marshall_dict(d.__dict__) for d in items]
        except BadQQuery:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! Format must follow 'key:value'."
                },
            )
        except exc.InvalidRequestError:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Bad q query param! key must contain valid columns"
                },
            )

    else:
        items = db.query(Type).offset(skip).limit(limit).all()
        items = [marshall_dict(d.__dict__) for d in items]
    return items


def get_single_type_with_session(db: Session, type_id) -> Optional[dict]:
    item = db.query(Type).filter(Type.id == type_id).first()
    if item is not None:
        return marshall_dict(item.__dict__)
    else:
        return None


def create_type_with_session(db: Session, type: TypePostModel) -> int:
    new_type = Type(**type.dict())
    db.add(new_type)
    # print((str(stmt)))
    # r = db.execute(stmt)
    db.commit()
    return new_type.id


def update_type_with_session(db: Session, type_id: int, type: TypePutModel) -> dict:
    update_dict = {k: v for k, v in type.dict().items() if v is not None}
    item_to_update = db.query(Type).filter(Type.id == type_id).update(update_dict)
    db.commit()
    return {"success": True}


def delete_type_with_session(db: Session, type_id: int) -> dict:
    el = db.query(Type).filter(Type.id == type_id).first()
    if el is not None:
        db.query(Type).filter_by(id=type_id).delete()
        db.commit()
        return {"success": True}
    else:
        raise DoesNotExist()


### APP ROUTES FOR Type
# Get Single
@app.get(
    "/type/{type_id}",
    response_model=TypeGetSingleModel,
    operation_id="get_single_type",
    tags=["Type"],
)
async def get_single_type(type_id: int, db: Session = Depends(get_db)):
    _item = get_single_type_with_session(db, type_id)
    if _item:
        return _item
    else:
        return JSONResponse(status_code=404, content={"message": "Not Found"})


# Get Many Resources
@app.get(
    "/type",
    response_model=List[TypeGetSingleModel],
    operation_id="get_many_type",
    tags=["Type"],
)
async def get_many_type(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
):
    return get_type_with_session(db, q=q)


# Create A Unique Resource
@app.post("/type", operation_id="create_single_type", tags=["Type"])
async def post_type(new_type: TypePostModel, db: Session = Depends(get_db)):
    try:
        return create_type_with_session(db, new_type)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Update A Unique Resource
@app.put("/type/{type_id}", operation_id="edit_single_type", tags=["Type"])
async def put_type(type_id: int, type: TypePutModel, db: Session = Depends(get_db)):
    try:
        return update_type_with_session(db, type_id, type)
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Delete A Unique Resource
@app.delete("/type/{type_id}", operation_id="delete_single_type", tags=["Type"])
async def delete_type(type_id: int, db: Session = Depends(get_db)):
    try:
        return delete_type_with_session(db, type_id)
    except DoesNotExist:
        return JSONResponse(
            status_code=404,
            content={"message": "type does not exist with id == " + str(type_id)},
        )
    except exc.IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=400, content={"succes": False, "error": e.orig.args[1]}
        )


# Data Models
class SqlViewModelOut(BaseModel):
    keys: List[str]
    rows: List[tuple]
    total: int


class AvailableViews(BaseModel):
    views: List[str]


def get_view_with_session(view, db, limit=100, offset=0):
    r = db.execute(f"SELECT * FROM {view} LIMIT {str(limit)} OFFSET {str(offset)}")
    x = r.fetchall()
    return {
        "keys": [str(s) for s in r.keys()],
        "rows": [tuple(r) for r in x],
        "total": len(x),
    }


def get_filtered_view_with_sessions(
    view, filter_key, filter_value, db, limit=100, offset=0
):
    if (filter_key is None) and (filter_value is None):
        raise BadQQuery()

    r = db.execute(f"SELECT * FROM {view} LIMIT 1 OFFSET 0")

    if not filter_key in [str(s) for s in r.keys()]:
        raise BadQQuery()

    t = text(
        f"SELECT * FROM {view} WHERE {filter_key} = :filter_value LIMIT :limit OFFSET :offset"
    )
    r = db.execute(
        t,
        {"view": view, "limit": limit, "offset": offset, "filter_value": filter_value},
    )
    x = r.fetchall()
    return {
        "keys": [str(s) for s in r.keys()],
        "rows": [tuple(r) for r in x],
        "total": len(x),
    }


@app.get(
    "/views/{view}",
    operation_id="query_view",
    tags=["SQL Views"],
    response_model=SqlViewModelOut,
)
async def query_sql_views(
    view: str,
    filter_key: Optional[str] = None,
    filter_value: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if view not in get_available_views_with_session(db):
        return JSONResponse(
            status_code=404,
            content={"succes": False, "error": "That view does not exist"},
        )

    try:
        if filter_key and filter_value:
            result = get_filtered_view_with_sessions(
                view, filter_key, filter_value, db, limit=100, offset=0
            )
        else:
            result = get_view_with_session(view, db, limit, offset)

        return result
    except BadQQuery as bq:
        return JSONResponse(
            status_code=400, content={"succes": False, "error": "Bad Query"}
        )


@app.get(
    "/views",
    operation_id="available_views",
    tags=["SQL Views"],
    response_model=AvailableViews,
)
async def query_sql_views(db: Session = Depends(get_db)):
    return {"views": get_available_views_with_session(db)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=8)
