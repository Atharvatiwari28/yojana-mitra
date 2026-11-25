"""
ask.py - terminal mein Yojana Mitra se baat karo 💬 (ab follow-up sawaal bhi samajhta hai!)

Chalao (yojana-mitra folder mein, venv on karke):
    python ask.py
"""

import rag

print("🤖 Yojana Mitra ready ho raha hai...")
rag.retrieve("PM-KISAN")  # warm-up: model + database pehle hi load (LLM call nahi, free!)
print("✅ Ready! 🇮🇳 Sawaal poocho (band karne ke liye 'exit', nayi baat ke liye 'reset')\n")

history = []  # 💬 is chat ki yaaddasht

while True:
    question = input("🙋 Sawaal: ").strip()
    if question.lower() in ("exit", "quit", ""):
        break
    if question.lower() == "reset":
        history = []
        print("🧹 Nayi baatcheet shuru!\n")
        continue

    result = rag.answer(question, history)
    print(f"   ✍️ Search question: {result['search_question']}")
    if result["evidence"]:
        print(f"\n📌 Document mein likha hai:\n{result['evidence']}")
    print(f"\n🤖 Yojana Mitra:\n{result['answer']}\n")
    print("   📚 Jo documents padhe gaye:")
    for c in result["chunks"]:
        print(f"      - {c['source']}, page {c['pages']}")
    print("\n" + "-" * 70 + "\n")

    # 💬 yaaddasht mein jodo
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": result["answer"]})

print("👋 Bye!")