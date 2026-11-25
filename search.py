"""
search.py (v2) - query rewriting ke saath search 🔍✍️

Har sawaal ke liye DO search karta hai, aur dono dikhata hai:
  A) 🙋 Seedha user ka sawaal (jaisa likha)
  B) ✍️ LLM (Groq) se English search-query mein badla hua sawaal

Isse dikhta hai ki query rewriting se search kitni sudhri 📊

Chalao (yojana-mitra folder mein, venv on karke):
    python search.py

.env mein GROQ_API_KEY bhi chahiye!
"""

import os

import groq
import psycopg
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

EMBED_MODEL = "intfloat/multilingual-e5-small"
LLM_MODEL = "openai/gpt-oss-120b"
TOP_K = 5

REWRITE_PROMPT = """You turn a user's question about Indian government schemes into a clear English question for searching official documents.
Rules:
- The user may write in Hinglish (Hindi in Roman script), Hindi, or English.
- Translate Hindi/Hinglish words to English (kisaan -> farmer, ghar -> house, paisa -> money, aay/kamaai -> income).
- If the question clearly refers to a scheme, mention its official name (e.g. PM-KISAN, PMAY-U 2.0).
- Write it as ONE complete, natural English question, not keywords.
- Example: "kisaan ko saal mein kitna paisa milta hai?" -> "How much money does a farmer receive per year under PM-KISAN?"
- Output ONLY the question, nothing else."""


def get_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def to_pgvector(numbers) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in numbers) + "]"


def rewrite_query(question: str) -> str:
    """✍️ LLM se sawaal ko search-friendly English mein badlo. Fail ho toh original hi lo."""
    try:
        response = ai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,   # 🧊 har baar same, predictable
            timeout=20,
        )
        return response.choices[0].message.content.strip()
    except groq.APIError as e:
        print(f"   ⚠️ Rewrite fail hua ({type(e).__name__}), original sawaal se search kar rahe hain")
        return question


def search(text: str):
    q_emb = model.encode("query: " + text, normalize_embeddings=True)
    cursor.execute(
        """
        SELECT source, pages, text, embedding <=> %s::vector AS doori
        FROM chunks
        ORDER BY doori
        LIMIT %s
        """,
        (to_pgvector(q_emb), TOP_K),
    )
    return cursor.fetchall()


def show(title: str, results):
    print(f"\n   {title}")
    for rank, (source, pages, text, doori) in enumerate(results, start=1):
        print(f"      #{rank}  📄 {source}  |  pages {pages}  |  doori {doori:.3f}")
        print("          " + text[:160].replace("\n", " ") + " ...")


print("🤖 Models load ho rahe hain...")
model = SentenceTransformer(EMBED_MODEL)
ai_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conn = get_conn()
cursor = conn.cursor()
print("✅ Ready! Sawaal poocho (band karne ke liye 'exit')\n")

while True:
    question = input("🙋 Sawaal: ").strip()
    if question.lower() in ("exit", "quit", ""):
        break

    rewritten = rewrite_query(question)
    print(f"   ✍️ Rewritten: {rewritten}")

    show("A) 🙋 Seedha sawaal se search:", search(question))
    show("B) ✍️ Rewritten sawaal se search:", search(rewritten))
    print("\n" + "-" * 70 + "\n")

conn.close()
print("👋 Bye!")