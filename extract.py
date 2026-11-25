import json
from pathlib import Path

from pypdf import PdfReader

PDF_FOLDER = Path("data/pdfs")
OUTPUT_FILE = Path("data/pages.json")

all_pages = []

for pdf_path in sorted(PDF_FOLDER.glob("*.pdf")):
    reader = PdfReader(pdf_path)
    print(f"📄 {pdf_path.name}: {len(reader.pages)} pages")

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        all_pages.append({
            "source": pdf_path.name,
            "page": page_number,
            "text": text,
            "needs_ocr": len(text) < 50,
        })

OUTPUT_FILE.write_text(json.dumps(all_pages, ensure_ascii=False, indent=2))

ocr_count = sum(1 for p in all_pages if p["needs_ocr"])
print(f"\n✅ {len(all_pages)} pages save hue → {OUTPUT_FILE}")
print(f"📷 {ocr_count} pages ko OCR chahiye (kal karenge!)")