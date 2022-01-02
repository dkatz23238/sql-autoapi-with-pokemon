from sqlalchemy import create_engine
import time

import sqlalchemy


import glob

views = glob.glob("./queries/*.sql")

view_names = [i.split("/")[-1].replace(".sql", "") for i in views]
view_parts = " ".join([f"('{V}') " for V in view_names])
insert_stmnt = "INSERT INTO available_sql_views (name) VALUES " + view_parts + ";"

def get_query(file):
    with open(file) as fh:
        return fh.read()


def __execute(conn, filename):
    rs = conn.execute(get_query(filename))
    try:
        for out in rs:
            print(out)
    except Exception as e:
        print(e)

    time.sleep(0.02)


if __name__ == "__main__":
    # connection
    engine = create_engine(
        "mysql://playground:playground@127.0.0.1:3306/playground")

    # create metadata
    with engine.connect() as conn:
        for q in views:
            print(q)
            __execute(conn, q)

        rs = conn.execute(insert_stmnt)
        print(rs)
        try:
            print([i for i in rs])
        except Exception as e:
            print(e)
