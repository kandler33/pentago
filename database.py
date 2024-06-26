import sqlite3
import os

from settings import settings


class Database:
    def __init__(self, db_filename: str) -> None:
        self.con = sqlite3.connect(db_filename)

    def get_from(self, table_name: str, **kwargs) -> dict:
        cur = self.con.cursor()
        sql_string = (
            f"SELECT * FROM {table_name}\nWHERE " +
            " AND ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
        )
        sql_string = sql_string.replace("None", "NULL")

        data = cur.execute(sql_string).fetchone()
        columns = (i[0] for i in cur.description)
        cur.close()
        return dict(zip(columns, data))

    def select_from(self, table_name: str, **kwargs) -> tuple:
        cur = self.con.cursor()
        sql_string = f"SELECT * FROM {table_name}\n"

        if kwargs:
            sql_string = (
                sql_string + "WHERE " +
                " AND ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
            )
        sql_string = sql_string.replace("None", "NULL")

        data = cur.execute(sql_string).fetchall()
        columns = [i[0] for i in cur.description]
        cur.close()
        return tuple(dict(zip(columns, row)) for row in data)

    def update(self, table_name: str, pk: int, **kwargs) -> None:
        cur = self.con.cursor()
        sql_string = (
            f"UPDATE {table_name}\nSET " +
            ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items()) +
            f"\nWHERE id={pk}"
        )
        sql_string = sql_string.replace("None", "NULL")

        cur.execute(sql_string)
        cur.close()


database = Database(os.path.join(settings.data_folder, settings.db_filename))
