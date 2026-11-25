"""
ocr.py - Tesseract se OCR 📷

2 kaam karta hai:
  1. needs_ocr wale pages pe OCR chalata hai. Kuch na mile toh page ko "blank" mark karta hai.
  2. PM-KISAN FAQ (purana, ganda OCR) ka fresh OCR karke dono ko compare karta hai.

Chalao (yojana-mitra folder mein, venv on karke):
    python ocr.py
"""

import json
from pathlib import Path

import pymupdf  # pymupdf ka naam code mein "fitz" hai
import pytesseract
from PIL import Image

PDF_FOLDER = Path("data/pdfs")
PAGES_FILE = Path("data/pages.json")
FAQ_FILE = "pm_kisan_faq.pdf"


def ocr_page(pdf_name: str, page_number: int) -> str:
    """PDF ka ek page → image 🖼️ → Tesseract 🔍 → text 📝"""
    pdf = pymupdf.open(PDF_FOLDER / pdf_name)
    page = pdf[page_number - 1]  # pymupdf 0 se ginta hai, hum 1 se!
    pix = page.get_pixmap(dpi=300)  # 300 DPI = saaf photo
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    pdf.close()
    return pytesseract.image_to_string(image, lang="eng").strip()


pages = json.loads(PAGES_FILE.read_text())

# ---------------------------------------------------------------
# Kaam 1: "khaali" pages verify karo 👀
# ---------------------------------------------------------------
print("👀 Kaam 1: text-less pages check kar rahe hain...\n")
for p in pages:
    if not p["needs_ocr"]:
        continue

    text = ocr_page(p["source"], p["page"])
    if len(text) < 20:
        p["blank"] = True
        print(f"   📄 {p['source']} page {p['page']}: KHAALI page hai (OCR ko bhi kuch nahi mila)")
    else:
        p["text"] = text
        p["method"] = "ocr"
        p["blank"] = False
        print(f"   📷 {p['source']} page {p['page']}: SCANNED tha! OCR se {len(text)} characters mile")

# ---------------------------------------------------------------
# Kaam 2: FAQ ka fresh OCR + compare 📊
# ---------------------------------------------------------------
print(f"\n📊 Kaam 2: {FAQ_FILE} ka fresh OCR...\n")

BAD_WORDS = ["PIV-KISAN", "PtV", "Frequentl v", "Ind ia"]  # purane OCR ki galtiyan jo humne dekhi


def count_bad(text: str) -> int:
    return sum(text.count(w) for w in BAD_WORDS)


old_total_bad = new_total_bad = 0
old_good = new_good = 0

for p in pages:
    if p["source"] != FAQ_FILE:
        continue

    new_text = ocr_page(p["source"], p["page"])
    p["text_ocr_fresh"] = new_text  # purana text mitao mat, dono rakho (compare ke liye)

    old_total_bad += count_bad(p["text"])
    new_total_bad += count_bad(new_text)
    old_good += p["text"].count("PM-KISAN")
    new_good += new_text.count("PM-KISAN")

    if p["page"] == 1:
        print("   --- Page 1: PURANA text (pehle 300 characters) ---")
        print("   " + p["text"][:300].replace("\n", "\n   "))
        print("\n   --- Page 1: NAYA OCR text (pehle 300 characters) ---")
        print("   " + new_text[:300].replace("\n", "\n   "))
        print()

print("   📊 Score (poori FAQ):")
print(f"      Galat words (PIV-KISAN, PtV...):   purana = {old_total_bad:3}   naya = {new_total_bad:3}   (kam = achha)")
print(f"      Sahi 'PM-KISAN' kitni baar mila:   purana = {old_good:3}   naya = {new_good:3}   (zyada = achha)")

PAGES_FILE.write_text(json.dumps(pages, ensure_ascii=False, indent=2))
print("\n💾 pages.json update ho gayi!")