"""
embed.py - chunks → embeddings (384 numbers) → pgvector mein save 🔢🐘

Kya karta hai:
  1. Docker wale PostgreSQL (port 5433) mein 'chunks' table banata hai
  2. multilingual-e5-small model se har chunk ka embedding banata hai
  3. Sab kuch database mein save karta hai (dobara chalane pe purana data hata ke naya)

Chalao (yojana-mitra folder mein, venv on karke):
    python embed.py

Pehli baar model download hoga (~450 MB), thoda time lagega ⏳
"""

import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

CHUNKS_FILE = Path("data/chunks.json")
MODEL_NAME = "intfloat/multilingual-e5-small"


def get_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def to_pgvector(numbers) -> str:
    """[0.12, -0.03, ...] → '[0.120000,-0.030000,...]' (pgvector is format ko samajhta hai)"""
    return "[" + ",".join(f"{x:.6f}" for x in numbers) + "]"


def main():
    chunks = json.loads(CHUNKS_FILE.read_text())
    print(f"📦 {len(chunks)} chunks load hue")

    # 1. 🤖 Model load (pehli baar download hoga)
    print(f"🤖 Model load ho raha hai: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    # 2. 🔢 Embeddings banao, "passage: " lagana zaroori hai (e5 ka rule!)
    texts = ["passage: " + c["text"] for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=32,              # 32-32 ke batch mein (fast + memory safe)
        normalize_embeddings=True,  # sab vectors ki "lambai" 1 kar do, cosine ke liye achha
        show_progress_bar=True,
    )
    print(f"✅ {len(embeddings)} embeddings bane, har ek mein {len(embeddings[0])} numbers")

    # 3. 🐘 Database mein save
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id         INTEGER PRIMARY KEY,
            source     TEXT NOT NULL,
            pages      INTEGER[] NOT NULL,
            text       TEXT NOT NULL,
            embedding  VECTOR(384) NOT NULL
        )
    """)
    cursor.execute("TRUNCATE chunks")  # dobara chalane pe purana data hatao, duplicate na bane

    rows = [
        (c["id"], c["source"], c["pages"], c["text"], to_pgvector(emb))
        for c, emb in zip(chunks, embeddings)
    ]
    cursor.executemany(
        "INSERT INTO chunks (id, source, pages, text, embedding) VALUES (%s, %s, %s, %s, %s::vector)",
        rows,
    )

    # ⚡ Index: lakhon chunks pe bhi search fast rahe
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS chunks_embedding_idx
        ON chunks USING hnsw (embedding vector_cosine_ops)
    """)

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM chunks")
    print(f"🐘 Database mein {cursor.fetchone()[0]} chunks save hue!")
    conn.close()


if __name__ == "__main__":
    main()