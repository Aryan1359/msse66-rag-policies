from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

@app.get("/")
def index():
    return "MSSE66 RAG — placeholder. Try GET /health"

if __name__ == "__main__":
    # Codespaces-friendly defaults
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
