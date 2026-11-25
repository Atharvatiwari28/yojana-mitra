"""
embed_gemini.py - chunks → Gemini embeddings (768 numbers) → pgvector 🔢🐘

Purana embed.py (e5-small) waise hi rakha hai, comparison ke liye.
Yeh naya script ek NAYI table 'chunks_gemini' banata hai, purani 'chunks' ko chhedta nahi.

Chalao (yojana-mitra folder mein, venv on karke):
    python embed_gemini.py

Free tier ki limit hai (100 requests/minute), isliye 20-20 ke batch mein
thoda ruk-ruk ke bhejte hain. Poora kaam ~5 minute ⏳
"""

import json
import time
from pathlib import Path

from db import get_conn
from embeddings import EMBED_DIM, embed_texts, to_pgvector

CHUNKS_FILE = Path("data/chunks.json")
TABLE = "chunks_gemini"
BATCH_SIZE = 20
PAUSE_SECONDS = 15  # 20 chunks × 4 batch/minute = 80/minute, limit (100) se neeche 🛡️


def main():
    chunks = json.loads(CHUNKS_FILE.read_text())
    print(f"📦 {len(chunks)} chunks load hue")

    embeddings = []
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = [c["text"] for c in chunks[start:start + BATCH_SIZE]]
        embeddings.extend(embed_texts(batch, "RETRIEVAL_DOCUMENT"))
        print(f"  🔢 {len(embeddings)}/{len(chunks)} ho gaye")
        if len(embeddings) < len(chunks):
            time.sleep(PAUSE_SECONDS)

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id         INTEGER PRIMARY KEY,
            source     TEXT NOT NULL,
            pages      INTEGER[] NOT NULL,
            text       TEXT NOT NULL,
            embedding  VECTOR({EMBED_DIM}) NOT NULL
        )
    """)
    cursor.execute(f"TRUNCATE {TABLE}")

    cursor.executemany(
        f"INSERT INTO {TABLE} (id, source, pages, text, embedding) VALUES (%s, %s, %s, %s, %s::vector)",
        [(c["id"], c["source"], c["pages"], c["text"], to_pgvector(e)) for c, e in zip(chunks, embeddings)],
    )
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS {TABLE}_embedding_idx
        ON {TABLE} USING hnsw (embedding vector_cosine_ops)
    """)
    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
    print(f"🐘 '{TABLE}' table mein {cursor.fetchone()[0]} chunks save hue!")
    conn.close()


if __name__ == "__main__":
    main()