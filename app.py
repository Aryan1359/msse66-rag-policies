from flask import Flask, jsonify, request
from pathlib import Path
import json, re, os

app = Flask(__name__)

@app.get("/")
def root():
    return "MSSE66 RAG — placeholder. Try GET /health", 200

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

# --- Minimal keyword search endpoint over JSONL index ---
INDEX_PATH = Path("data/index/policies.jsonl")

def _load_index(path: Path):
    recs = []
    if not path.exists():
        return recs
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs

def _score(text: str, terms):
    s = 0
    for t in terms:
        if not t:
            continue
        s += len(re.findall(rf"\b{re.escape(t)}\b", text, flags=re.I))
    return s

def _search(recs, query: str, topk: int = 3):
    terms = [t.strip() for t in query.split() if t.strip()]
    scored = []
    for r in recs:
        sc = _score(r.get("text",""), terms)
        if sc > 0:
            scored.append((sc, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:topk]]

@app.get("/search")
def search_endpoint():
    q = request.args.get("q", "").strip()
    try:
        topk = int(request.args.get("topk", "3"))
    except ValueError:
        topk = 3

    if not q:
        return jsonify({"error":"Missing query param 'q'"}), 400
    recs = _load_index(INDEX_PATH)
    if not recs:
        return jsonify({"error": f"Index not found at {INDEX_PATH}. Run scripts/index_jsonl.py."}), 500

    hits = _search(recs, q, topk=topk)
    return jsonify({
        "query": q,
        "topk": topk,
        "count": len(hits),
        "results": [
            {
                "id": h.get("id"),
                "doc_id": h.get("doc_id"),
                "source": h.get("source"),
                "tokens_rough": h.get("tokens_rough"),
                "preview": re.sub(r"\s+", " ", h.get("text",""))[:200]
            } for h in hits
        ]
    })

if __name__ == "__main__":
    # Default to port 8000 in Codespaces
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=False)
