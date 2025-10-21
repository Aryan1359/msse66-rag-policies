
# MSSE66 RAG — Company Policies Q&A

## 🌐 Live Demo
Deployed on Render (Free Tier):  
https://msse66-rag-policies.onrender.com

**Health check**
```bash
curl -sS https://msse66-rag-policies.onrender.com/health
````

**Sample question**

**Features:**
* Fast keyword retrieval (local, simple)
* Grounded answers with citations (`sources[]`)
* Automated evaluation & CI gate (groundedness, citation, latency)
* One-click deploy on Render (Procfile + gunicorn)
* Extractive summary (LLM disabled)


```bash
curl -sS -X POST https://msse66-rag-policies.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the PTO policy?"}'
```

---


---

## 🤝 How to contribute

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---
## 🧭 Overview

A Retrieval-Augmented Generation (RAG) app that answers questions about a small corpus of **company policies**.
Focus areas:

* **Ingestion & keyword retrieval** (local, simple & fast)
* **Grounded answers** with citations via `sources[]`
* **Automated evaluation & CI gate** (groundedness, citation accuracy, latency)
* **One-click deploy** on Render (Procfile + `gunicorn`)

Current `/ask` behavior: **extractive summary** (LLM disabled), with returned `sources[]` for grounding.

---

## ✅ Current Status (v0.7.1)

* Endpoints: `/`, `/health`, `/search`, `/ask`
* Keyword retrieval working end-to-end
* `/ask` returns: `answer`, `question`, `sources[]`, `source_labels`, timing fields
* **Evaluation Gate** in CI with thresholds (p95 latency + grounding/citation rates)
* Deployment scaffold merged; live service on **Render**

Tag history:
`v0.4.0` (RAG synthesis scaffold) → `v0.5.0` (eval hook) → `v0.6.0` (CI gate) → `v0.7.0` (deploy scaffold) → **`v0.7.1` (Live Demo docs)**

---

## 🚀 Quickstart (Local / Codespaces)

```bash
# 1) Activate virtual env
source .venv/bin/activate

# 2) (Re)build the lightweight keyword index
python scripts/index_jsonl.py

# 3) Run the Flask app on port 8000
python app.py
```

**Test endpoints (local):**

```bash
# Health
curl "http://127.0.0.1:8000/health"

# Keyword search
curl "http://127.0.0.1:8000/search?q=pto%20policy&topk=3"

# Ask (POST)
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the PTO policy?"}'
```

> Using Codespaces preview? Open the forwarded URL like `https://<id>-8000.app.github.dev/`.

---

## 🧩 API

### GET `/health`

Returns `{"status":"ok"}`.

### GET `/search`

Query string parameters:

| Param  | Type   | Default   | Description                             |
| :----- | :----- | :-------- | :-------------------------------------- |
| `q`    | string | —         | Query text                              |
| `topk` | int    | `3`       | Number of results                       |
| `mode` | string | `keyword` | Retrieval mode (`keyword` or `vector`)* |

> *Vector mode is scaffolded; keyword is the default and used in production today.

**Response shape (example):**

```json
{
  "mode": "keyword",
  "query": "pto policy",
  "topk": 3,
  "results": [
    {"doc_id":"01-pto","chunk_id":1,"score":5.0,"preview":"# Paid Time Off …"}
  ],
  "sources": [{"doc_id":"01-pto","chunk_id":1}]
}
```

### POST `/ask`

Body:

```json
{"question": "<your question>", "topk": 4}
```

**Response shape (example):**

```json
{
  "answer": "…extractive summary…",
  "question": "What is the PTO policy?",
  "retrieval_ms": 18,
  "llm_ms": 0,
  "model": "disabled",
  "source_labels": {"S1":{"doc_id":"01-pto","chunk_id":1}},
  "sources": [
    {"doc_id":"01-pto","chunk_id":1,"score":0.0}
  ],
  "tokens": 0
}
```

---

## 📊 Evaluation & CI Gate

Automated evaluation for `/ask` lives in **`scripts/eval_ask.py`** and is wired into CI (**`.github/workflows/eval.yml`**).

**Metrics**

* **Groundedness**: % of answers returning a non-empty `sources[]`.
* **Citation Accuracy**: (heuristic) at least one cited source matches returned sources.
* **Latency**: end-to-end time; we report p50 and p95 (ms) without NumPy.

**Thresholds (defaults)**

* `--min-grounded 0.75`
* `--min-citation 0.75`
* `--p95-total 4000` (ms)

The gate **fails** (exit code `2`) if any threshold is missed.

**Run locally**

```bash
# quick sample
python scripts/eval_ask.py --limit 5

# full gate with defaults
make eval-gate

# override thresholds
MIN_GROUNDED=0.8 MIN_CITATION=0.8 P95_MS=3500 make eval-gate
```

**Artifacts** (written locally and uploaded in CI)

* `data/eval/latest_metrics.json` — machine-readable summary + per-item results
* `data/eval/latest_metrics.md` — human-readable report

---

## 📁 Repository Structure

```
msse66-rag-policies/
├─ app.py                      # Flask app (/, /health, /search, /ask)
├─ data/
│  ├─ policies/                # Markdown policy docs
│  └─ index/                   # Built indexes (keyword; vector hooks)
├─ scripts/
│  ├─ index_jsonl.py           # Build keyword index
│  ├─ search_jsonl.py          # Local keyword search CLI
│  ├─ embed_index.py           # (scaffold) Build embeddings
│  ├─ vector_search.py         # (scaffold) Cosine similarity search
│  └─ eval_ask.py              # Eval metrics + CI gate (p95, thresholds, artifacts)
├─ .github/workflows/eval.yml  # Evaluation workflow
├─ Makefile                    # `make eval-gate`
├─ Procfile                    # Production entrypoint (gunicorn)
├─ render/render.yaml          # Render service config (free plan)
├─ requirements.txt
├─ PROGRESS-LOG.md
├─ LEARNING-GUIDE.md
├─ checklist.md
└─ Instruction.md
```

---

## 🚀 Deployment (Render Free Tier)

Included:

* `Procfile` → `gunicorn app:app --bind 0.0.0.0:${PORT} --timeout 120`
* `render/render.yaml` (free plan)
* `requirements.txt` includes `gunicorn`

One-time setup:

1. In Render: **New → Web Service → select repo**
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app --bind 0.0.0.0:${PORT} --timeout 120`
4. Health check path: `/health`
5. Env vars: `PYTHON_VERSION=3.12.1`, `FLASK_ENV=production`

**Local prod-like run**

```bash
pip install -r requirements.txt
PORT=8000 gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
# open http://127.0.0.1:8000/health
```

---

## 👤 Maintainer

* Aryan Yaghobi — [https://github.com/Aryan1359](https://github.com/Aryan1359)

````
