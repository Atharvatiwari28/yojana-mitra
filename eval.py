"""
eval.py - Yojana Mitra ka report card 📊🎓

eval_set.json ke har sawaal pe Yojana Mitra chalata hai, aur 4 cheezein naapta hai:
  1. 🔍 Retrieval hit:   sahi PDF ka chunk top 5 mein aaya?
  2. ✅ Answer correct:  jawab mein zaroori facts hain? (jaise "6000")
  3. 📄 Citation ok:     jawab ne sahi PDF ko source bataya?
  4. 🙅 Refusal:         trap sawaalon pe "nahi mili" bola? (aur asli sawaalon pe galti se mana toh nahi kiya?)

Chalao (yojana-mitra folder mein, venv on karke):
    python eval.py

Har run ka poora result evals/results_<time>.json mein save hota hai, taaki
pehle aur baad compare kar sako 📈
"""

import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import rag

EVAL_FILE = Path("eval_set.json")
RESULTS_DIR = Path("evals")


def norm(text: str) -> str:
    """Compare ke liye: ajeeb spaces/hyphens normal karo, chhote letters, commas aur ₹ hatao
    ("₹10,000" → "10000", non-breaking space → normal space)"""
    text = unicodedata.normalize("NFKC", text)  # non-breaking space → normal space
    text = text.replace("‐", "-").replace("‑", "-")  # ajeeb hyphens → normal "-"
    text = text.lower().replace(",", "").replace("₹", "").replace("rs.", "")
    return " ".join(text.split())  # bahut saare spaces → ek


def is_refusal(answer: str) -> bool:
    return "nahi mili" in answer.lower()


def check(item: dict, result: dict) -> dict:
    answer = result["answer"]
    retrieved_sources = {c["source"] for c in result["chunks"]}

    if item.get("trap"):
        return {"trap": True, "refused": is_refusal(answer)}

    expected = set(item["expected_sources"])
    must_ok = all(
        any(norm(word) in norm(answer) for word in group)
        for group in item["must_include"]
    )
    return {
        "trap": False,
        "retrieval_hit": bool(expected & retrieved_sources),
        "answer_correct": must_ok and not is_refusal(answer),
        "citation_ok": any(f"source: {s}" in answer.lower() for s in expected),
        "false_refusal": is_refusal(answer),
    }


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "-"


def main():
    items = json.loads(EVAL_FILE.read_text())
    print(f"📊 {len(items)} sawaalon pe test shuru...\n")

    rows = []
    for item in items:
        result = rag.answer(item["question"])
        score = check(item, result)
        rows.append({**item, **score, "search_question": result["search_question"],
                     "evidence": result.get("evidence", ""),
                     "answer": result["answer"],
                     "retrieved": [f"{c['source']} p{c['pages']}" for c in result["chunks"]]})

        if score["trap"]:
            mark = "✅" if score["refused"] else "❌"
            print(f"{mark} #{item['id']:>2} 🪤 TRAP  | mana kiya: {score['refused']} | {item['question']}")
        else:
            mark = "✅" if score["answer_correct"] else "❌"
            print(f"{mark} #{item['id']:>2} answer: {score['answer_correct']!s:5} | "
                  f"retrieval: {score['retrieval_hit']!s:5} | citation: {score['citation_ok']!s:5} | {item['question']}")
        time.sleep(1)  # Groq free limit ka dhyan 🙏

    real = [r for r in rows if not r["trap"]]
    traps = [r for r in rows if r["trap"]]

    print("\n" + "=" * 70)
    print("🎓 YOJANA MITRA REPORT CARD")
    print("=" * 70)
    print(f"   🔍 Retrieval hit (sahi PDF top 5 mein):  {pct(sum(r['retrieval_hit'] for r in real), len(real))}")
    print(f"   ✅ Answer accuracy:                      {pct(sum(r['answer_correct'] for r in real), len(real))}")
    print(f"   📄 Citation accuracy:                    {pct(sum(r['citation_ok'] for r in real), len(real))}")
    print(f"   🙅 Trap pe sahi mana kiya:               {pct(sum(r['refused'] for r in traps), len(traps))}")
    print(f"   ⚠️  Asli sawaal pe galti se mana kiya:    {pct(sum(r['false_refusal'] for r in real), len(real))}")

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"results_{datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"\n💾 Poora result (har jawab ke saath): {out}")
    print("   ❌ wale sawaalon ke jawab us file mein padho, wahi agla improvement batayenge! 🕵️")


if __name__ == "__main__":
    main()