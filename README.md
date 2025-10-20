# MSSE66 RAG — Company Policies Q&A

Retrieval‑Augmented Generation (RAG) app that answers questions about a small corpus of **company policies**. Built as part of the **MSSE66+ AI Engineering Project**, aligned to the rubric (environment, CI, ingestion, retrieval, embeddings, evaluation).

---

## 📌 Status (end of Phase 3)

✅ Repo + CI green
✅ Keyword retrieval working (`/search?mode=keyword`)
✅ Local sentence‑transformer embeddings created (`all‑MiniLM‑L6‑v2`)
✅ Vector retrieval working (`/search?mode=vector`)
✅ Consistent JSON responses (`mode`, `query`, `topk`, `results`, `doc_id`, `chunk_id`, `score`, `preview`)
✅ Next step → add `sources` array + mini evaluation dataset

---

## 🚀 Quickstart (GitHub Codespaces)

```bash
# 1) Activate virtual env
source .venv/bin/activate

# 2) (Re)build JSONL index if policies changed
python scripts/index_jsonl.py

# 3) Generate embeddings (if not yet done)
python scripts/embed_index.py

# 4) Run the Flask app (port 8000)
python app.py
```

**Test endpoints:**

```bash
# Health check
curl "http://127.0.0.1:8000/health"

# Keyword search (default)
curl "http://127.0.0.1:8000/search?q=pto%20accrual&topk=3"

# Vector search
curl "http://127.0.0.1:8000/search?q=pto%20accrual%20policy&mode=vector&topk=3"
```

>  If you’re using Codespaces browser preview, use your forwarded URL like `https://<id>-8000.app.github.dev/`.

---

## 📁 Repository Structure

```
msse66‑rag‑policies/
├─ app.py                        # Flask app (/, /health, /search)
├─ data/
│  ├─ policies/                    # Markdown policy documents
│  │  ├─ 01‑pto.md
│  │  ├─ 02‑expenses.md
│  │  └─ 03‑remote‑work.md
│  └─ index/
│    ├─ policies.jsonl            # Chunked index
│    ├─ policies.npy              # Embedding matrix
│    └─ meta.json                  # Model metadata + id map
├─ scripts/
│  ├─ ingest.py                  # Document stats
│  ├─ chunk.py                   # Overlapping chunker
│  ├─ index_jsonl.py            # Build index
│  ├─ embed_index.py            # Encode chunks → vectors
│  └─ vector_search.py         # NumPy cosine retriever
├─ .github/workflows/ci.yml        # CI smoke test
├─ requirements.txt
├─ Instruction.md
├─ LEARNING‑GUIDE.md
├─ checklist.md
└─ PROGRESS‑LOG.md
```

---

## 🧩 Implemented Endpoints

### GET `/health`
→ `{"status":"ok"}`

### GET `/search`

|  Param   |  Type    |  Default    |  Description                          |
| :------- | :------- | :---------- | :------------------------------------ |
|  `q`     |  string  |  —          |  Query text                           |
|  `topk`  |  int     |  3          |  Top‑k results                        |
|  `mode`  |  string  |  `keyword`  |  Search type (`keyword` or `vector`)  |

**Example (keyword):**

```bash
curl "http://127.0.0.1:8000/search?q=vacation%20policy&topk=3"
```

Response:

```json
{
 "mode": "keyword",
 "query": "vacation policy",
 "topk": 3,
 "results": [
  {"doc_id": "01‑pto", "chunk_id": 1, "score": 5.0, "preview": "# Paid Time Off…"}
 ]
}
```

**Example (vector):**

```bash
curl "http://127.0.0.1:8000/search?q=pto%20accrual%20policy&mode=vector&topk=3"
```

Response:

```json
{
 "mode": "vector",
 "query": "pto accrual policy",
 "topk": 3,
 "results": [
  {"doc_id": "01‑pto", "chunk_id": 1, "score": 0.65, "preview": "# Paid Time Off…"},
  {"doc_id": "02‑expenses", "chunk_id": 1, "score": 0.42, "preview": "# Employee Expense…"}
 ]
}
```

---

## 🧠 Phase Summary

|  Phase  |  Goal                           |  Key Outputs                                         |
| :------ | :------------------------------ | :--------------------------------------------------- |
|  1      |  Environment + Flask setup      |  `app.py` (/, /health)                               |
|  2      |  Ingestion + keyword retrieval  |  `policies.jsonl`, `/search?mode=keyword`            |
|  3      |  Embeddings + vector search     |  `policies.npy`, `meta.json`, `/search?mode=vector`  |
|  4      |  Answer synthesis (LLM)         |  pending                                             |
|  5      |  Evaluation metrics             |  pending                                             |
|  6      |  Deployment (Render/Vercel)     |  pending                                             |

---

## 🧮 Dependencies

```
Flask==3.0.3
python‑dotenv==1.0.1
sentence‑transformers==2.7.0
numpy==1.26.4
```

---

## 🧭 Next Phase Plan

1️⃣ Add `sources` array to each response (`[{doc_id, chunk_id}]`).
2️⃣ Keep default `mode=keyword`, document `mode=vector`.
3️⃣ Seed tiny Q&A evaluation dataset (`data/eval/`).
4️⃣ Add CI latency + groundedness metrics.

---

## Phase 3 additions

### `/search` now includes `sources[]`
The search API returns a compact citation list for evaluation and RAG:
```json
{
  "mode": "keyword",
  "query": "pto accrual",
  "results": [ ... ],
  "topk": 3,
  "sources": [{"doc_id": "01-pto", "chunk_id": 1}]
}
```

### Tiny evaluation

Seed set (5 items): `data/eval/qa_sample.json`

Run the evaluator against the local server:

```bash
python app.py
# in another shell:
python scripts/eval.py --qa data/eval/qa_sample.json --base-url http://127.0.0.1:8000 --mode keyword --topk 3
```

Outputs per-item overlap and a latency roll-up:

```
[summary] hits=5/5 (100%)
[latency] min=..ms p50=..ms avg=..ms p95~=..ms
```

---

## Phase 4 – RAG Answer Synthesis (WIP)


## Phase 4 – RAG Answer Synthesis

### scripts/generate_answer.py (retrieval → prompt → LLM → citations)

- End-to-end RAG answer generation: retrieves top policy chunks, builds a prompt, calls the LLM (if configured), and post-processes the answer.
- If LLM is not configured, falls back to extractive summary with a clear note.
- CLI usage (module mode recommended):

  ```bash
  python -m scripts.generate_answer --q "What’s our PTO carryover limit?" --topk 3
  # Retrieval modes:
  #   RETRIEVAL_MODE=keyword (default, no embeddings needed)
  #   RETRIEVAL_MODE=http (calls /search?mode=vector)
  #   RETRIEVAL_MODE=vector (local, needs embeddings)
  ```

### /ask endpoint (POST + GET)

- Unified endpoint for RAG answer synthesis.
- Returns JSON with:
  - `question`, `answer`, `sources`, `source_labels`, `retrieval_ms`, `llm_ms`, `model`, `tokens`
- `source_labels` is a mapping `{S1: {doc_id, chunk_id}, ...}` matching the order of `sources[]`.
- **Citation format:** Answers include inline `[S1]`, `[S2]`, ... that correspond 1:1 to the returned `sources[]` and `source_labels`.

#### Quickstart

Run server:

```bash
python app.py
```

Ask a question (POST):

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How do holidays accrue?","topk":4}' | jq
```

Ask a question (GET):

```bash
curl -s "http://127.0.0.1:8000/ask?q=PTO%20accrual%20policy%3F&topk=3" | jq
```

CLI generator (module mode):

```bash
python -m scripts.generate_answer --q "What’s our PTO carryover limit?" --topk 3
```

#### Retrieval modes

Set the environment variable `RETRIEVAL_MODE=keyword|http|vector` (default: `keyword`).

```bash
# default keyword (no embeddings required)
python -m scripts.generate_answer --q "PTO accrual policy?" --topk 4

# force HTTP vector (server must be running)
RETRIEVAL_MODE=http python -m scripts.generate_answer --q "PTO accrual policy?" --topk 4

# force local vector (requires embeddings available)
RETRIEVAL_MODE=vector python -m scripts.generate_answer --q "PTO accrual policy?" --topk 4
```

#### LLM configuration

- `GROQ_API_KEY` (required for LLM calls)
- `RAG_MODEL` (default: llama-3.1-8b-instruct)
- `RAG_MAX_TOKENS` (default: 512)
- If no API key is present, the system falls back to extractive summary with a note: `(LLM disabled; extractive summary)`

#### Troubleshooting

- If 404 on `/ask`: kill old process, restart with `python app.py`.
- If zero hits: ensure `data/index/policies.jsonl` exists (rebuild with `python scripts/index_jsonl.py`) and try `RETRIEVAL_MODE=keyword`.
