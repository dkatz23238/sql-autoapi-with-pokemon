import inspect
import json
import os

import sqlalchemy
from jinja2 import Template
from jinja2.filters import FILTERS, pass_environment

import datamodels.models as models
from datamodels.models import Base

_tplt = open("./j2templates/fastapi.py.jinja2").read()

def get_default_bool(c):
    if c.default:
        return True
    else:
        return False


def get_fk_bool(c):
    if c.foreign_keys:
        return True
    else:
        return False


def sqlalchemy_type_to_python(t: object) -> str:
    if isinstance(t, sqlalchemy.String):
        return "str"
    if isinstance(t, sqlalchemy.Integer):
        return "int"
    if isinstance(t, sqlalchemy.DateTime):
        return "datetime.datetime"
    if isinstance(t, sqlalchemy.Float):
        return "float"
    if isinstance(t, sqlalchemy.Float):
        return "float"
    if isinstance(t, sqlalchemy.Boolean):
        return "bool"


api_tables = [
    j
    for i, j in inspect.getmembers(models)
    if isinstance(j, sqlalchemy.orm.decl_api.DeclarativeMeta) and j != Base
]


api_table_names = [t.__tablename__ for t in api_tables]
api_table_columns = []

for apitable in api_tables:

    columns = []
    for c in apitable.__table__.columns:

        col = {
            "name": c.name,
            "type": sqlalchemy_type_to_python(c.type),
            "is_pk": c.primary_key,
            "is_nullable": c.nullable,
            "is_fk": get_fk_bool(c),
            "has_default": get_default_bool(c),
        }

        if c.foreign_keys:
            _keys = [fk for fk in c.foreign_keys]
            k = _keys[0]
            foreign_key_target_full_name = k.target_fullname.split(".")
            col["_ftable"] = foreign_key_target_full_name[0]
            col["_fcol"] = foreign_key_target_full_name[1]

        columns.append(col)

    api_table_columns.append(columns)


@pass_environment
def snake_to_caps(_, value):
    """
    custom max calculation logic
    """
    _t = [i.capitalize() for i in value.split("_")]
    return "".join(_t)


@pass_environment
def snake_to_camel(_, value):
    """ snake_case to camelCase """
    _vals = value.split("_")
    camel_case = _vals[0] + "".join([i.capitalize() for i in _vals[1:]])
    return camel_case


if __name__ == "__main__":
    FILTERS["snake_to_caps"] = snake_to_caps

    api_tables = {k: v for k, v in list(
        zip(api_table_names, api_table_columns))}

    with open("api_tables.spec.json", "w") as f:
        f.write(json.dumps(api_tables, indent=2))

    template = Template(_tplt)

    with open("app.py", "w") as f:
        f.write(template.render(api_tables=api_tables))

    # Clean up
    os.system("black app.py")
