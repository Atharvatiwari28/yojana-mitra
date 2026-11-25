"""
db.py - Database connection, ek jagah 🐘

Local pe: .env ke DB_HOST / DB_PORT / ... use hote hain (Docker wala Postgres)
Live pe:  DATABASE_URL (Neon cloud ka ek lamba link) use hota hai

Code same rehta hai, sirf setting badalti hai (wahi .env wala funda 😉)
"""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg.connect(url)
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )