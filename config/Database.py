from datetime import datetime
import os
import uuid
from dotenv import load_dotenv
import pymysqlpool
import psycopg2.pool 
load_dotenv()
mydb= {
    "host": os.getenv("PGHOST"),
    "port": int(os.getenv("PGPORT")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "database": os.getenv("PGDATABASE"),
    "minconn": 1,  # Minimum number of connections in the pool
    "maxconn": 30,
}
pool = psycopg2.pool.SimpleConnectionPool(**mydb)
