import os
import json
import time
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
POLICIES_DIR = os.path.join("data", "policies")

# Register Step 4 blueprint
from steps.step4.step4_routes import step4_bp
app.register_blueprint(step4_bp)
ALLOWED_EXTS = {".md", ".txt", ".pdf"}

def _infer_name(rec):
    for k in ("source", "path", "file"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return os.path.basename(v)
    meta = rec.get("meta") or {}
    for k in ("source", "path", "file"):
        v = meta.get(k)
        if isinstance(v, str) and v.strip():
            return os.path.basename(v)
    v = rec.get("doc_id") or meta.get("doc_id")
    if isinstance(v, str) and v.strip():
        return v
    return "unknown"

def _list_files_payload():
    files = {}
    if os.path.exists(INDEX_JSONL):
        with open(INDEX_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                name = _infer_name(rec)
                info = files.setdefault(name, {"name": name, "chunk_count": 0, "mtime": None})
                info["chunk_count"] += 1
    for name, info in files.items():
        p = os.path.join(POLICIES_DIR, name)
        if os.path.exists(p):
            try:
                info["mtime"] = os.path.getmtime(p)
                info["size"] = os.path.getsize(p)
            except Exception:
                info["mtime"] = None
                info["size"] = None
    return {"files": sorted(files.values(), key=lambda x: x["name"].lower()), "count": len(files)}

def _allowed(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTS

    if not os.path.exists(p):
        return jsonify({"ok": False, "error": "not found"}), 404
    return send_from_directory(POLICIES_DIR, name)

@app.route("/", methods=["GET"])
def ui_home():
    return render_template("index.html")

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
    answer_text = res.get("answer", "")
    sources = res.get("sources", [])
    # Build a clean sources array for frontend rendering
    sources_list = []
    for i, s in enumerate(sources, 1):
        sources_list.append({
            "label": f"S{i}",
            "doc_id": s.get("doc_id", "?"),
            "chunk_id": s.get("chunk_id", "?"),
            "score": s.get("score", 0)
        })
    payload = {
        "question": res.get("question", question),
        "answer": answer_text,
        "sources": sources_list,
        "retrieval_ms": res.get("retrieval_ms", 0),
        "llm_ms": res.get("llm_ms", 0),
        "model": res.get("model", ""),
        "tokens": res.get("tokens", 0),
    }
    return jsonify(payload), 200


# Step 2: Show all files in a table format
@app.route("/steps/2", methods=["GET"])
def step_2_page():
    files = []
    for fname in os.listdir(POLICIES_DIR):
        ext = os.path.splitext(fname)[1].lower()
        if ext in {".md", ".txt", ".pdf", ".html", ".htm"}:
            files.append({
                "doc_id": fname,
                "ext": ext,
                "size": os.path.getsize(os.path.join(POLICIES_DIR, fname)),
            })
    return render_template("steps/step_2.html", files=files)

@app.route("/steps/<int:step_id>", methods=["GET"])
def step_page(step_id):
    if step_id == 2:
        return step_2_page()
    if not (1 <= step_id <= 20):
        abort(404)
    return render_template(f"steps/step_{step_id}.html", step_id=step_id)

from routes.files import files_bp
app.register_blueprint(files_bp)

from steps.step5.step5_routes import step5_bp
app.register_blueprint(step5_bp)
from routes.step2 import step2_bp
app.register_blueprint(step2_bp)
from routes.step3 import step3_bp
app.register_blueprint(step3_bp)
from steps.step6.step6_routes import step6_bp
app.register_blueprint(step6_bp)

# Register Step 7 blueprint
from steps.step7.step7_routes import step7_bp
app.register_blueprint(step7_bp)

if __name__ == "__main__":
    print('Registered routes:', app.url_map, file=sys.stderr)
    app.run(host="0.0.0.0", port=8000)
