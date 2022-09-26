import logging
import os

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# set logger to be configurable from external
logger = logging.getLogger("api-demo-server")

DB_HOST = os.environ.get("DEMO_SERVER_DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DEMO_SERVER_DB_PORT", "5432")

DB_USER = os.environ.get("DEMO_SERVER_DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DEMO_SERVER_DB_PASSWORD", "mysecretpassword")


class DataBase:
    def __init__(self):
        self.db_conn = None
        self.db_cursor = None
        self.psql_conn = psycopg2.connect(
            user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        self.psql_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.psql_cursor = self.psql_conn.cursor()

    def db_exists(self, name):
        self.psql_cursor.execute(
            "select exists(select * from pg_database where datname=%s)", (name,)
        )
        if self.psql_cursor.fetchone()[0]:
            logger.info(f"Database '{name}' already exists.")
            return True
        return False

    def connect_to_db(self, db_name):
        self.create_db(db_name)

        self.db_conn = psycopg2.connect(
            dbname=db_name,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        self.db_cursor = self.db_conn.cursor()

        logger.info(f"Successfully connected to database: {db_name}")

    def create_db(self, db_name):
        if not self.db_exists(db_name):
            # Prevent sql injection attack by using sql module instead of string concat
            self.psql_cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

    def drop_db(self, db_name):
        # Prevent sql injection attack by using sql module instead of string concat
        self.psql_cursor.execute(
            sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
        )
        if not self.db_exists(db_name):
            self.db_conn = None
            self.db_cursor = None
            logger.info(f"Database '{db_name}' was successfully removed")

    def table_exists(self, table_name):
        self.db_cursor.execute(
            "SELECT EXISTS (SELECT relname FROM pg_class WHERE relname=%s);", (table_name,)
        )
        if self.db_cursor.fetchone()[0]:
            logger.info(f"Table '{table_name}' already exists.")
            return True
        return False

    def create_table(self):
        if self.db_cursor is None:
            self.connect_to_db("names_db")
        if self.table_exists("names"):
            return
        self.db_cursor.execute("CREATE TABLE names (id serial PRIMARY KEY, data varchar);")
        self.db_conn.commit()

    def add_name(self, name):
        self.create_table()
        self.db_cursor.execute("INSERT INTO names (data) VALUES (%s)", (name,))
        self.db_conn.commit()

    @property
    def all_names(self):
        self.create_table()
        self.db_cursor.execute("SELECT * FROM names;")
        return self.db_cursor.fetchall()
