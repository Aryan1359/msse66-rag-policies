import csv
from datetime import datetime
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- Step 2: Parse and Clean Functions ---
def parse_file(doc_id):
    ext = os.path.splitext(doc_id)[1].lower()
    
import csv
from datetime import datetime
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

INDEX_JSONL = os.path.join("data", "index", "policies.jsonl")
POLICIES_DIR = os.path.join("data", "policies")
ALLOWED_EXTS = {".md", ".txt", ".pdf"}
PARSED_DIR = os.path.join("data", "parsed")
PARSED_STATS_CSV = os.path.join("data", "index", "parsed_stats.csv")
PARSE_LOG = os.path.join("logs", "parse.jsonl")

app = Flask(__name__)
    src_path = os.path.join(POLICIES_DIR, doc_id)
    out_path = os.path.join(PARSED_DIR, doc_id + ".txt")
    result = {"doc_id": doc_id, "ok": False, "error": None, "chars": 0}
    try:
        os.makedirs(PARSED_DIR, exist_ok=True)
        if not os.path.exists(src_path):
            raise Exception("File not found")
        if ext == ".pdf":
            from pdfminer.high_level import extract_text
            text = extract_text(src_path)
        elif ext in {".html", ".htm"}:
            from bs4 import BeautifulSoup
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "lxml")
                for tag in soup(["script", "style"]): tag.decompose()
                text = soup.get_text(separator="\n")
        elif ext in {".md", ".txt"}:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            raise Exception("Unsupported file type")
        result["chars"] = len(text)
        result["ok"] = True
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        result["error"] = str(e)
    return result

def clean_file(doc_id):
    out_path = os.path.join(PARSED_DIR, doc_id + ".txt")
    result = {"doc_id": doc_id, "ok": False, "error": None, "cleaned_chars": 0}
    try:
        if not os.path.exists(out_path):
            raise Exception("Parsed file not found")
        with open(out_path, "r", encoding="utf-8") as f:
            text = f.read()
        # Simple clean: remove extra blank lines and trim
        cleaned = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        result["cleaned_chars"] = len(cleaned)
        result["ok"] = True
    except Exception as e:
        result["error"] = str(e)
    return result

# API endpoints for parse/clean single and all files
# --- Step 2: Parse and Clean Functions ---
def parse_file(doc_id):
    ext = os.path.splitext(doc_id)[1].lower()
    src_path = os.path.join(POLICIES_DIR, doc_id)
    out_path = os.path.join(PARSED_DIR, doc_id + ".txt")
    result = {"doc_id": doc_id, "ok": False, "error": None, "chars": 0}
    try:
        os.makedirs(PARSED_DIR, exist_ok=True)
        if not os.path.exists(src_path):
            raise Exception("File not found")
        if ext == ".pdf":
            from pdfminer.high_level import extract_text
            text = extract_text(src_path)
        elif ext in {".html", ".htm"}:
            from bs4 import BeautifulSoup
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "lxml")
                for tag in soup(["script", "style"]): tag.decompose()
                text = soup.get_text(separator="\n")
        elif ext in {".md", ".txt"}:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            raise Exception("Unsupported file type")
        result["chars"] = len(text)
        result["ok"] = True
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        result["error"] = str(e)
    return result

def clean_file(doc_id):
    out_path = os.path.join(PARSED_DIR, doc_id + ".txt")
    result = {"doc_id": doc_id, "ok": False, "error": None, "cleaned_chars": 0}
    try:
        if not os.path.exists(out_path):
            raise Exception("Parsed file not found")
        with open(out_path, "r", encoding="utf-8") as f:
            text = f.read()
        # Simple clean: remove extra blank lines and trim
        cleaned = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        result["cleaned_chars"] = len(cleaned)
        result["ok"] = True
    except Exception as e:
        result["error"] = str(e)
    return result

# API endpoints for parse/clean single and all files
@app.route("/api/step2/parse", methods=["POST"])
def api_step2_parse():
    data = request.get_json(silent=True) or {}
    doc_id = data.get("doc_id")
    if not doc_id:
        return {"ok": False, "error": "Missing doc_id"}, 400
    result = parse_file(doc_id)
    return jsonify(result)

@app.route("/api/step2/clean", methods=["POST"])
def api_step2_clean():
    data = request.get_json(silent=True) or {}
    doc_id = data.get("doc_id")
    if not doc_id:
        return {"ok": False, "error": "Missing doc_id"}, 400
    result = clean_file(doc_id)
    return jsonify(result)

@app.route("/api/step2/parse_clean_all", methods=["POST"])
def api_step2_parse_clean_all():
    files = [f for f in os.listdir(POLICIES_DIR) if os.path.splitext(f)[1].lower() in {".md", ".txt", ".pdf", ".html", ".htm"}]
    results = []
    for doc_id in files:
        parse_res = parse_file(doc_id)
        clean_res = clean_file(doc_id) if parse_res["ok"] else {"ok": False, "error": "Parse failed"}
        results.append({"doc_id": doc_id, "parse": parse_res, "clean": clean_res})
    return jsonify(results)
import csv
from datetime import datetime
import os
import csv
from datetime import datetime
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
INDEX_JSONL = os.path.join("data", "index", "policies.jsonl")
POLICIES_DIR = os.path.join("data", "policies")
ALLOWED_EXTS = {".md", ".txt", ".pdf"}
PARSED_DIR = os.path.join("data", "parsed")
PARSED_STATS_CSV = os.path.join("data", "index", "parsed_stats.csv")
PARSE_LOG = os.path.join("logs", "parse.jsonl")

app = Flask(__name__)
app.register_blueprint(step2_api)

import csv
from datetime import datetime
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

INDEX_JSONL = os.path.join("data", "index", "policies.jsonl")
POLICIES_DIR = os.path.join("data", "policies")
ALLOWED_EXTS = {".md", ".txt", ".pdf"}
PARSED_DIR = os.path.join("data", "parsed")
PARSED_STATS_CSV = os.path.join("data", "index", "parsed_stats.csv")
PARSE_LOG = os.path.join("logs", "parse.jsonl")

app = Flask(__name__)

# --- Step 2: Modular File Listing Endpoint ---
@app.route("/api/step2/files", methods=["GET"])
def api_step2_files():
    files = []
    for fname in os.listdir(POLICIES_DIR):
        ext = os.path.splitext(fname)[1].lower()
        if ext in {".md", ".txt", ".pdf", ".html", ".htm"}:
            files.append({
                "doc_id": fname,
                "ext": ext,
                "size": os.path.getsize(os.path.join(POLICIES_DIR, fname)),
            })
    return jsonify(files), 200

import csv
from datetime import datetime
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

INDEX_JSONL = os.path.join("data", "index", "policies.jsonl")
POLICIES_DIR = os.path.join("data", "policies")
ALLOWED_EXTS = {".md", ".txt", ".pdf"}
PARSED_DIR = os.path.join("data", "parsed")
PARSED_STATS_CSV = os.path.join("data", "index", "parsed_stats.csv")
PARSE_LOG = os.path.join("logs", "parse.jsonl")

app = Flask(__name__)


@app.route("/api/parse", methods=["POST"])
def api_parse():
    data = request.get_json(silent=True) or {}
    doc_ids = data.get("doc_ids")
    if not doc_ids:
        doc_ids = _get_uploaded_files()
    parsed, errors = [], []
    for doc_id in doc_ids:
        res = _parse_file(doc_id)
        if res["ok"]:
            parsed.append(doc_id)
        else:
            errors.append({"doc_id": doc_id, "error": res["error"]})
    _update_parsed_stats()
    return jsonify({"parsed": parsed, "errors": errors}), 200

@app.route("/api/parsed/<doc_id>", methods=["GET"])
def api_parsed(doc_id):
    safe_id = secure_filename(doc_id)
    parsed_path = os.path.join(PARSED_DIR, safe_id + ".txt")
    if not os.path.exists(parsed_path):
        return "Not parsed yet.", 404
    with open(parsed_path, "r", encoding="utf-8") as f:
        txt = f.read()
    return txt, 200, {"Content-Type": "text/plain; charset=utf-8"}
import os
import json
import time
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename
app = Flask(__name__)

# --- Files API (list + upload) ---
INDEX_JSONL = os.path.join("data", "index", "policies.jsonl")
POLICIES_DIR = os.path.join("data", "policies")
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

@app.route("/api/files", methods=["GET", "POST"])
def api_files():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "missing file"}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "empty filename"}), 400
        name = secure_filename(f.filename)
        if not _allowed(name):
            return jsonify({"ok": False, "error": "unsupported extension"}), 400
        os.makedirs(POLICIES_DIR, exist_ok=True)
        dst = os.path.join(POLICIES_DIR, name)
        f.save(dst)
        # Rebuild index
        import subprocess
        subprocess.run(["python", "scripts/index_jsonl.py"], check=True)
        # Fall through to return the updated list with 201
        payload = _list_files_payload()
        return jsonify(payload), 201
    # GET
    payload = _list_files_payload()
    return jsonify(payload), 200




@app.route("/api/files/<path:fname>", methods=["DELETE"])
def api_files_delete(fname):
    name = secure_filename(os.path.basename(fname))
    if not name:
        return jsonify({"ok": False, "error": "invalid name"}), 400
    p = os.path.join(POLICIES_DIR, name)
    if not os.path.exists(p):
        return jsonify({"ok": False, "error": "not found"}), 404
    # Delete the file
    try:
        os.remove(p)
    except Exception as e:
        return jsonify({"ok": False, "error": f"delete failed: {e}"}), 500
    # Rebuild index
    import subprocess
    subprocess.run(["python", "scripts/index_jsonl.py"], check=True)
    # Return updated list
    return jsonify(_list_files_payload()), 200


# Serve raw files for download/view
@app.route("/api/files/raw/<path:fname>", methods=["GET"])
def api_files_raw(fname):
    name = secure_filename(os.path.basename(fname))
    p = os.path.join(POLICIES_DIR, name)
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

if __name__ == "__main__":
    print('Registered routes:', app.url_map, file=sys.stderr)
    app.run(host="0.0.0.0", port=8000)
