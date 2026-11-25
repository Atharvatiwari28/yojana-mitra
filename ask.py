"""
ask.py - terminal mein Yojana Mitra se baat karo 💬

Saara RAG code ab rag.py mein hai, yeh file sirf chat chalati hai.

Chalao (yojana-mitra folder mein, venv on karke):
    python ask.py
"""

import rag

print("🤖 Yojana Mitra ready ho raha hai...")
rag.retrieve("PM-KISAN")  # warm-up: model + database pehle hi load (LLM call nahi, free!)
print("✅ Ready! 🇮🇳 Sawaal poocho (band karne ke liye 'exit')\n")

while True:
    question = input("🙋 Sawaal: ").strip()
    if question.lower() in ("exit", "quit", ""):
        break

    result = rag.answer(question)
    print(f"   ✍️ Search question: {result['search_question']}")
    if result["evidence"]:
        print(f"\n📌 Document mein likha hai:\n{result['evidence']}")
    print(f"\n🤖 Yojana Mitra:\n{result['answer']}\n")
    print("   📚 Jo documents padhe gaye:")
    for c in result["chunks"]:
        print(f"      - {c['source']}, page {c['pages']}")
    print("\n" + "-" * 70 + "\n")

print("👋 Bye!")