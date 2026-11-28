"""
chunk.py - saaf pages ko chhote tukdon (chunks) mein todo ✂️

Rules:
  - Har chunk lagbhag MAX_CHARS characters ka
  - Sentence ke beech mein kabhi nahi kaatna, hamesha sentence ke end pe
  - Overlap: naya chunk pichle chunk ke aakhri OVERLAP_SENTENCES sentences se shuru hota hai 🔗
  - Har chunk yaad rakhta hai ki woh kis PDF ke kaunse pages se aaya 📄
  - Ek chunk kabhi do alag PDFs ko mix nahi karta

Output: data/chunks.json

Chalao (yojana-mitra folder mein, venv on karke):
    python chunk.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

CLEAN_FILE = Path("data/clean_pages.json")
OUTPUT_FILE = Path("data/chunks.json")

MAX_CHARS = 1000        # 📏 chunk ka size
OVERLAP_SENTENCES = 2   # 🔗 kitne sentences agle chunk mein dohraane hain


def split_sentences(text: str) -> list[str]:
    """Page ka text → sentences ki list"""
    text = re.sub(r"\n(?!\n)", " ", text)  # PDF ki tooti lines jodo (paragraph break rehne do)
    parts = re.split(r"(?<=[.!?])\s+|\n\n+", text)  # "." "!" "?" ke baad, ya paragraph pe kaato
    sentences = []
    for s in parts:
        s = s.strip()
        if len(s) <= 1:
            continue
        # Bahut lamba "sentence" (jaise bina full-stop wali table)? Words pe tod do
        while len(s) > MAX_CHARS:
            cut = s.rfind(" ", 0, MAX_CHARS)
            cut = cut if cut > 0 else MAX_CHARS
            sentences.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            sentences.append(s)
    return sentences


def make_chunks(pages: list[dict]) -> list[dict]:
    """[{"source", "page", "text"}, ...] → chunks. Upload wali PDF (user_docs.py) bhi yahi use karti hai 🔁"""
    # Har PDF ke sentences, unke page number ke saath: [(sentence, page), ...]
    sentences_by_source = defaultdict(list)
    for p in pages:
        for sentence in split_sentences(p["text"]):
            sentences_by_source[p["source"]].append((sentence, p["page"]))

    chunks = []
    for source, sentences in sentences_by_source.items():
        current = []  # abhi ke chunk ke sentences: [(sentence, page), ...]

        def save_chunk():
            text = " ".join(s for s, _ in current)
            pages_in_chunk = sorted({pg for _, pg in current})
            chunks.append({
                "id": len(chunks) + 1,
                "source": source,
                "pages": pages_in_chunk,
                "text": text,
            })

        for sentence, page in sentences:
            current_len = sum(len(s) + 1 for s, _ in current)
            if current and current_len + len(sentence) > MAX_CHARS:
                save_chunk()
                current = current[-OVERLAP_SENTENCES:]  # 🔗 overlap
                # agar overlap hi bahut bada ho, toh use chhota karo
                while current and sum(len(s) + 1 for s, _ in current) + len(sentence) > MAX_CHARS:
                    current = current[1:]
            current.append((sentence, page))

        if current:
            save_chunk()
    return chunks


def main():
    pages = json.loads(CLEAN_FILE.read_text())
    chunks = make_chunks(pages)
    sources = list(dict.fromkeys(c["source"] for c in chunks))

    OUTPUT_FILE.write_text(json.dumps(chunks, ensure_ascii=False, indent=2))

    # 📊 Report
    lengths = [len(c["text"]) for c in chunks]
    print("✂️  Chunking report\n")
    for source in sources:
        n = sum(1 for c in chunks if c["source"] == source)
        print(f"   📄 {source}: {n} chunks")
    print(f"\n   🧩 Total chunks:   {len(chunks)}")
    print(f"   📏 Size (chars):   avg {sum(lengths) // len(lengths)}, "
          f"min {min(lengths)}, max {max(lengths)}")
    multi = sum(1 for c in chunks if len(c["pages"]) > 1)
    print(f"   📄📄 Do pages mein phaile chunks: {multi}")

    sample = chunks[len(chunks) // 2]
    print(f"\n   👀 Ek sample chunk (#{sample['id']}, {sample['source']}, pages {sample['pages']}):")
    print("   " + sample["text"][:400] + " ...")

    print(f"\n💾 Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()