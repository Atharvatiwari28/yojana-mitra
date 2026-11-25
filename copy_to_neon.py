"""
copy_to_neon.py - Local Docker DB ki 'chunks_gemini' table → Neon (cloud) 📦→☁️

Embeddings dobara nahi banate (Gemini ka quota bachao 💰), bas rows copy karte hain.

Chalne se pehle .env mein dono hone chahiye:
    DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD   → local (yahan se padhenge)
    DATABASE_URL                                          → Neon (yahan likhenge)

Chalao:
    python copy_to_neon.py
"""

import os

import psycopg
from dotenv import load_dotenv

from embeddings import EMBED_DIM

load_dotenv()

TABLE = "chunks_gemini"


def main():
    # 1. 💻 Local se padho (DB_* settings, DATABASE_URL ko ignore karke)
    local = psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
    )
    with local.cursor() as cur:
        # embedding::text → '[0.12,-0.03,...]' string, jo Neon wapas ::vector bana dega
        cur.execute(f"SELECT id, source, pages, text, embedding::text FROM {TABLE} ORDER BY id")
        rows = cur.fetchall()
    local.close()
    print(f"💻 Local se {len(rows)} rows padhi")

    # 2. ☁️ Neon mein likho
    neon_url = os.getenv("DATABASE_URL")
    if not neon_url:
        raise SystemExit("❌ .env mein DATABASE_URL nahi mila (Neon ka connection string daalo)")

    with psycopg.connect(neon_url) as neon, neon.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id         INTEGER PRIMARY KEY,
                source     TEXT NOT NULL,
                pages      INTEGER[] NOT NULL,
                text       TEXT NOT NULL,
                embedding  VECTOR({EMBED_DIM}) NOT NULL
            )
        """)
        cur.execute(f"TRUNCATE {TABLE}")
        cur.executemany(
            f"INSERT INTO {TABLE} (id, source, pages, text, embedding) VALUES (%s, %s, %s, %s, %s::vector)",
            rows,
        )
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {TABLE}_embedding_idx
            ON {TABLE} USING hnsw (embedding vector_cosine_ops)
        """)
        cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
        print(f"☁️ Neon mein {cur.fetchone()[0]} rows pahunch gayi! 🎉")
    # 'with' block khatam hote hi commit apne aap ho jata hai ✅


if __name__ == "__main__":
    main()