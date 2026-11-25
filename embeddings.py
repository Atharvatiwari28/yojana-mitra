"""
embeddings.py - Text → numbers, Google Gemini API se 🔢☁️

Pehle hum e5-small model apne laptop pe chalate the (torch + ~1 GB RAM).
Free server sirf 512 MB deta hai, isliye ab embeddings API se banwate hain:
server pe koi model nahi, sirf ek HTTP call ⚡

Do tarah ke embeddings (e5 mein "query:" / "passage:" jaisa hi idea):
  RETRIEVAL_DOCUMENT → PDF ke chunks ke liye
  RETRIEVAL_QUERY    → user ke sawaal ke liye
"""

import os
import time

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768  # 3072 bhi ho sakta hai, lekin 768 kaafi hai aur database chhota rehta hai

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def embed_texts(texts: list[str], task_type: str, retries: int = 3) -> list[list[float]]:
    """Kai texts ek saath → har text ka 768 numbers wala normalized vector"""
    for attempt in range(retries + 1):
        try:
            result = _get_client().models.embed_content(
                model=EMBED_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBED_DIM),
            )
            break
        except errors.ClientError as e:
            if e.code == 429 and attempt < retries:  # ⏳ rate limit: thoda ruko, phir try
                print("⏳ Rate limit lagi, 60 second ruk raha hoon...")
                time.sleep(60)
                continue
            raise

    vectors = []
    for e in result.embeddings:
        v = np.array(e.values, dtype=np.float32)
        v = v / np.linalg.norm(v)  # 3072 se kam dimension pe khud normalize karna padta hai
        vectors.append(v.tolist())
    return vectors


def embed_query(question: str) -> list[float]:
    return embed_texts([question], "RETRIEVAL_QUERY")[0]


def to_pgvector(numbers) -> str:
    """[0.12, -0.03, ...] → '[0.120000,-0.030000,...]' (pgvector is format ko samajhta hai)"""
    return "[" + ",".join(f"{x:.6f}" for x in numbers) + "]"
