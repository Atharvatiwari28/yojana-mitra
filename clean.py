"""
clean.py - pages.json ka text saaf karo 🧹

Kya karta hai:
  1. 🏆 Har page ka best text chunta hai (FAQ ke liye fresh OCR)
  2. 📄 Khaali pages hataata hai
  3. 🧹 Har page pe repeat hone wale headers/footers aur akele page numbers hataata hai
  4. 🔧 Line ke end pe toote words jodta hai ("Govern-\nment" → "Government")
  5. ✨ Faltu spaces, akele "|" jaise kachre, ajeeb characters saaf karta hai

Output: data/clean_pages.json

Chalao (yojana-mitra folder mein, venv on karke):
    python clean.py
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PAGES_FILE = Path("data/pages.json")
OUTPUT_FILE = Path("data/clean_pages.json")

HEADER_MIN_SHARE = 0.25  # line kam se kam 25% pages pe aaye...
HEADER_MIN_PAGES = 3     # ...aur kam se kam 3 pages pe, tab header maano
HEADER_MAX_LEN = 100     # headers chhote hote hain


def best_text(page: dict) -> str:
    """🏆 Fresh OCR hai toh woh lo (better quality), warna original"""
    return page.get("text_ocr_fresh") or page["text"]


def normalize(text: str) -> str:
    """✨ Ajeeb characters ko normal karo"""
    text = unicodedata.normalize("NFKC", text)  # "ﬁ" → "fi", full-width chars → normal
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return text


def find_headers(pages: list[dict]) -> dict[str, set[str]]:
    """🔍 Har PDF mein woh lines dhoondo jo bahut saare pages pe repeat hoti hain"""
    lines_per_source = defaultdict(Counter)
    pages_per_source = Counter()

    for p in pages:
        pages_per_source[p["source"]] += 1
        unique_lines = {line.strip() for line in p["text"].splitlines() if line.strip()}
        for line in unique_lines:
            if len(line) <= HEADER_MAX_LEN:
                lines_per_source[p["source"]][line] += 1

    headers = {}
    for source, counter in lines_per_source.items():
        min_pages = max(HEADER_MIN_PAGES, int(pages_per_source[source] * HEADER_MIN_SHARE))
        headers[source] = {line for line, count in counter.items() if count >= min_pages}
    return headers


def clean_text(text: str, header_lines: set[str]) -> str:
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in header_lines:
            continue                                  # 🧹 header/footer
        if re.fullmatch(r"\d{1,3}", stripped):
            continue                                  # 🧹 akela page number ("5")
        stripped = re.sub(r"\s*\|\s*$", "", stripped)   # 🧹 line ke end pe "|"
        stripped = re.sub(r"^\s*\|\s*", "", stripped)   # 🧹 line ke shuru mein "|"
        kept.append(stripped)

    text = "\n".join(kept)
    text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)   # 🔧 "Govern-\nment" → "Government"
    text = re.sub(r"[ \t]+", " ", text)               # ✨ bahut saare spaces → ek
    text = re.sub(r"\n{3,}", "\n\n", text)            # ✨ bahut saari khaali lines → ek
    return text.strip()


def main():
    raw_pages = json.loads(PAGES_FILE.read_text())

    # 1 + 2: best text chuno, khaali pages hatao
    pages = []
    skipped_blank = 0
    for p in raw_pages:
        if p.get("blank"):
            skipped_blank += 1
            continue
        text = normalize(best_text(p))
        if len(text.strip()) < 20:
            skipped_blank += 1
            continue
        method = "ocr" if (p.get("text_ocr_fresh") or p.get("method") == "ocr") else "pdf_text"
        pages.append({"source": p["source"], "page": p["page"], "text": text, "method": method})

    # 3: headers dhoondo
    headers = find_headers(pages)

    # 3 + 4 + 5: saaf karo
    chars_before = sum(len(p["text"]) for p in pages)
    for p in pages:
        p["text"] = clean_text(p["text"], headers[p["source"]])
    pages = [p for p in pages if len(p["text"]) >= 20]
    chars_after = sum(len(p["text"]) for p in pages)

    OUTPUT_FILE.write_text(json.dumps(pages, ensure_ascii=False, indent=2))

    # 📊 Report
    print("🧹 Cleaning report\n")
    print(f"   📄 Pages andar aaye:      {len(raw_pages)}")
    print(f"   🗑️  Khaali pages hataaye:  {skipped_blank}")
    print(f"   ✅ Saaf pages bache:      {len(pages)}")
    print(f"   ✂️  Characters:            {chars_before:,} → {chars_after:,} "
          f"({100 * (chars_before - chars_after) / chars_before:.1f}% kachra hataaya)\n")

    print("   🔍 Har page pe repeat hone wale headers (hata diye):")
    for source, lines in headers.items():
        print(f"      {source}:")
        if not lines:
            print("         (koi nahi mila)")
        for line in sorted(lines):
            print(f"         - {line!r}")

    print(f"\n💾 Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()