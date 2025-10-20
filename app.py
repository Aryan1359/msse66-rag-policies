
from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "OK", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/search", methods=["GET"])
def search_route():
    # Lightweight search endpoint, avoid heavy imports at module import
    q = request.args.get("q", "").strip()
    topk = int(request.args.get("topk", 3))
    mode = request.args.get("mode", "keyword").lower()
    if not q:
        return jsonify({"error": "missing q"}), 400
    # Only import heavy modules if needed
    if mode == "vector":
        from scripts.vector_search import search as vector_search
        results = vector_search(q, topk=topk)
        sources = [
            {"doc_id": r.get("doc_id"), "chunk_id": int(r.get("chunk_id", 0))}
            for r in results
            if r.get("doc_id") is not None
        ]
        payload = {
            "mode": "vector",
            "query": q,
            "results": results,
            "topk": topk,
            "sources": sources,
        }
        return jsonify(payload), 200
    else:
        import scripts.search_jsonl
        from pathlib import Path
        import os
        index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "index", "policies.jsonl")
        recs = scripts.search_jsonl.load_index(Path(index_path))
        results = scripts.search_jsonl.search(recs, q, topk=topk)
        sources = [
            {"doc_id": r.get("doc_id"), "chunk_id": int(r.get("chunk_id", 0))}
            for r in results
            if r.get("doc_id") is not None
        ]
        payload = {
            "mode": "keyword",
            "query": q,
            "results": results,
            "topk": topk,
            "sources": sources,
        }
        return jsonify(payload), 200

@app.route("/ask", methods=["POST", "GET"])
def ask():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        topk = int(data.get("topk") or 4)
    else:
        question = (request.args.get("q") or request.args.get("question") or "").strip()
        topk = int(request.args.get("topk") or 4)
    if not question:
        return jsonify({"error": "question is required"}), 400
    from scripts.generate_answer import run as rag_run
    res = rag_run(question, topk=topk)
    source_labels = {f"S{i+1}": {"doc_id": s["doc_id"], "chunk_id": s["chunk_id"]} for i, s in enumerate(res.get("sources", []))}
    payload = {
        "question": res.get("question", question),
        "answer": res.get("answer", ""),
        "sources": res.get("sources", []),
        "source_labels": source_labels,
        "retrieval_ms": res.get("retrieval_ms", 0),
        "llm_ms": res.get("llm_ms", 0),
        "model": res.get("model", ""),
        "tokens": res.get("tokens", 0),
    }
    return jsonify(payload), 200

if __name__ == "__main__":
    print(app.url_map, file=sys.stderr)
    app.run(host="0.0.0.0", port=8000)
