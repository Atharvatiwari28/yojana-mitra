"""
check_pdfs.py - har PDF check karo: text hai ya scanned? 🔍

Chalao (yojana-mitra folder mein, venv on karke):
    python check_pdfs.py
"""

from pathlib import Path

from pypdf import PdfReader

PDF_FOLDER = Path("data/pdfs")

for pdf_path in sorted(PDF_FOLDER.glob("*.pdf")):
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"❌ {pdf_path.name}: khul nahi payi ({e})")
        continue

    total_pages = len(reader.pages)
    text_pages = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        if len(text.strip()) > 50:   # 50+ characters mile = asli text wala page
            text_pages += 1

    if text_pages == total_pages:
        kind = "✅ TEXT PDF"
    elif text_pages == 0:
        kind = "📷 SCANNED PDF (OCR chahiye)"
    else:
        kind = f"🔀 MIXED ({total_pages - text_pages} page scanned)"

    print(f"{kind:32} | {total_pages:3} pages | {pdf_path.name}")