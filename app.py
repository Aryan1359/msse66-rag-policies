from flask import Flask, jsonify, request
from functools import lru_cache
from pathlib import Path
import os, re, json
import numpy as np
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

# --- Paths ---
INDEX_JSONL = Path("data/index/policies.jsonl")
EMB_NPY     = Path("data/index/policies.npy")
META_JSON   = Path("data/index/meta.json")

# --- Shared helpers ---
def _read_jsonl(path: Path):
    if not path.exists():
        return []
    recs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs

# =============================
# Keyword (bag-of-words) search
# =============================
def _kw_score(text: str, terms):
    s = 0
    for t in terms:
        if not t:
            continue
        s += len(re.findall(rf"\b{re.escape(t)}\b", text, flags=re.I))
    return s

def _keyword_search(recs, query: str, topk: int = 3):
    terms = [t.strip() for t in query.split() if t.strip()]
    scored = []
    for r in recs:
        sc = _kw_score(r.get("text", ""), terms)
        if sc > 0:
            scored.append((sc, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for sc, r in scored[:topk]:
        preview = (r.get("text", "")[:160].replace("\n", " ") + "…") if r else ""
        out.append({
            "doc_id": r.get("doc_id"),
            "chunk_id": r.get("chunk_id"),
            "id": r.get("id"),
            "score": float(sc),
            "preview": preview,
        })
    return out

# =====================
# Vector (semantic) search
# =====================
@lru_cache(maxsize=1)
def _load_vec_index():
    if not (INDEX_JSONL.exists() and EMB_NPY.exists() and META_JSON.exists()):
        return None
    mat  = np.load(EMB_NPY)  # [N,D], rows are L2-normalized
    meta = json.load(META_JSON.open("r", encoding="utf-8"))
    recs = _read_jsonl(INDEX_JSONL)
    model = SentenceTransformer(meta["model_name"], device="cpu")
    return (mat, meta, recs, model)

def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec) + 1e-12
    return (vec / n).astype(np.float32)

def _vector_search(query: str, topk: int = 3):
    loaded = _load_vec_index()
    if loaded is None:
        return {"error": "vector index not built. Run scripts/embed_index.py."}, 400
    mat, meta, recs, model = loaded
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=False)[0].astype(np.float32)
    q = _l2_normalize(q)
    scores = mat @ q  # cosine similarity (rows are normalized)
    idx = np.argsort(-scores)[:topk]

    results = []
    id_map = meta["id_map"]
    for i in idx:
        m = id_map[i]
        r = next((rr for rr in recs if rr.get("id") == m["id"]), None)
        preview = (r.get("text", "")[:160].replace("\n", " ") + "…") if r else ""
        results.append({
            "doc_id": m.get("doc_id"),
            "chunk_id": m.get("chunk_id"),
            "id": m.get("id"),
            "score": float(scores[i]),
            "preview": preview,
        })
    return {"mode": "vector", "query": query, "topk": topk, "results": results}, 200

# ============
# HTTP routes
# ============
@app.get("/")
def root():
    return "MSSE66 RAG — placeholder. Try GET /health", 200

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/search")
def search():
    q = request.args.get("q", "").strip()
    topk = int(request.args.get("topk", 3))
    mode = request.args.get("mode", "keyword").lower()

    if not q:
        return jsonify({"error": "missing q"}), 400

    if mode == "vector":
        payload, code = _vector_search(q, topk)
        # build compact sources list from results (doc_id + chunk_id)
        results = payload.get("results", []) if isinstance(payload, dict) else []
        sources = [
            {"doc_id": r.get("doc_id"), "chunk_id": int(r.get("chunk_id", 0))}
            for r in results
            if r.get("doc_id") is not None
        ]
        payload["sources"] = sources
        return jsonify(payload), code

    # keyword (default)
    recs = _read_jsonl(INDEX_JSONL)
    if not recs:
        return jsonify({"error": f"missing index: {INDEX_JSONL}"}), 400
    results = _keyword_search(recs, q, topk)
    # compact sources list
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


if __name__ == "__main__":
    # Default to port 8000 in Codespaces
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=False)
