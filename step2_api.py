from flask import Blueprint, jsonify
import os

POLICIES_DIR = os.path.join("data", "policies")

step2_api = Blueprint('step2_api', __name__)

@step2_api.route("/api/step2/files", methods=["GET"])
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
