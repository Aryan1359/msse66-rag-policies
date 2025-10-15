# MSSE66 RAG — Company Policies Q&A

Retrieval‑Augmented Generation (RAG) app that answers questions about a small corpus of **company policies**. Built as part of the **MSSE66+ AI Engineering Project** and aligned to the rubric (env + CI, ingestion, retrieval, deploy, evaluation).

---

## 📌 Status (end of Phase 2)

**Done:**

* Repo + Codespaces, `.venv`, Python pinned (3.12.1 via `.python-version`, `runtime.txt`)
* Minimal deps: `Flask`, `python-dotenv`
* Flask endpoints: `/` and `/health`
* CI: `.github/workflows/ci.yml` smoke‑tests `import app`
* Corpus: `data/policies/*.md` (PTO, Expenses, Remote Work)
* Ingestion & Indexing scripts:

  * `scripts/ingest.py` → doc stats
  * `scripts/chunk.py` → overlapping chunks
  * `scripts/index_jsonl.py` → writes `data/index/policies.jsonl`
  * `scripts/search_jsonl.py` → tiny keyword search (CLI)
* API: `/search?q=...&topk=...` returns keyword‑matched chunks (JSON)

**Next:** Phase 3 (Embeddings + vector search) → Phase 4 (UI) → Phase 5 (Deploy) → Phase 6 (Eval)

---

## 🚀 Quickstart (GitHub Codespaces)

```bash
# 1) Activate the virtualenv
source .venv/bin/activate

# 2) (Re)build JSONL index if you changed policies
python scripts/index_jsonl.py

# 3) Run the app (serves on port 8000)
python app.py
```

**Test locally from the terminal inside Codespaces:**

```bash
# Health
curl "http://127.0.0.1:8000/health"

# Keyword search
curl "http://127.0.0.1:8000/search?q=pto%20accrual&topk=3"
```

> In the browser, use your **forwarded URL** (looks like `https://<id>-8000.app.github.dev/`). In the terminal, prefer `http://127.0.0.1:8000`.

---

## 🧩 What’s implemented (Phase 2)

* **Corpus** in `data/policies/`: small, legal‑to‑use Markdown files.
* **Loader (`scripts/ingest.py`)** prints words/lines/headings per file.
* **Chunker (`scripts/chunk.py`)** creates ~600‑char chunks with ~100‑char overlap, preferring breaks on blank lines/headings.
* **Index writer (`scripts/index_jsonl.py`)** emits one JSON object per chunk to `data/index/policies.jsonl` with ids, text, and rough token counts.
* **Keyword search (CLI)** scores by simple term frequencies with word boundaries.
* **Flask `/search`** mirrors the CLI search and returns top‑k results with previews and metadata.

---

## 📁 Repository Structure

```
msse66-rag-policies/
├─ app.py                          # Flask app with /, /health, /search
├─ data/
│  ├─ policies/                    # Policy corpus (Markdown)
│  │  ├─ 01-pto.md
│  │  ├─ 02-expenses.md
│  │  └─ 03-remote-work.md
│  └─ index/
│     └─ policies.jsonl            # Generated JSONL index (build via scripts)
├─ scripts/
│  ├─ ingest.py                    # Corpus stats
│  ├─ chunk.py                     # Overlapping chunker
│  ├─ index_jsonl.py               # Write JSONL index
│  └─ search_jsonl.py              # CLI keyword search over JSONL
├─ .github/workflows/ci.yml        # CI: install deps + smoke test
├─ requirements.txt
├─ .python-version
├─ runtime.txt
├─ Instruction.md                  # Mentor/working-mode instructions
├─ LEARNING-GUIDE.md               # Beginner guide (what/why/how)
├─ checklist.md                    # Master checklist (rubric aligned)
└─ PROGRESS-LOG.md                 # Chronological log
```

---

## 🔄 Branch / PR Workflow (beginner‑proof)

1. Create a feature branch: `git checkout -b <feature>`
2. Make a tiny change; verify locally
3. `git add ... && git commit -m "<scope>: <message>"`
4. `git push -u origin <feature>` → Open PR → Merge → Delete branch
5. Sync: `git checkout main && git pull`

---

## 🧪 Verification Cheatsheet

```bash
# Stats
python scripts/ingest.py

# Chunking
python scripts/chunk.py

# Index build
python scripts/index_jsonl.py && wc -l data/index/policies.jsonl

# CLI search
python scripts/search_jsonl.py "pto accrual" --topk 3

# API search
curl "http://127.0.0.1:8000/search?q=pto%20accrual&topk=3"
```

---

## 🧭 Roadmap (Phases 3–6)

**Phase 3 — Embeddings & Vector Search**

* Choose embeddings: local (`sentence-transformers`) vs API provider
* `scripts/embed_index.py` → create vectors (e.g., `.npy` + `meta.json`)
* `scripts/vector_search.py` → cosine similarity top‑k
* Extend Flask `/search?mode=vector` with citations (doc_id + chunk_id)

**Phase 4 — Web UI**

* Minimal search page calling `/search`
* Display sources + highlighted snippets

**Phase 5 — Deployment & CI/CD**

* Deploy on Render/Railway (free tier)
* GH Actions: deploy on `main`

**Phase 6 — Evaluation**

* 15–30 Q/A set over policies
* Metrics: groundedness, citation accuracy, latency (p50/p95)
* Report in `design-and-evaluation.md`

---

## 🛠️ Troubleshooting

* `ModuleNotFoundError: flask` → `source .venv/bin/activate`
* 404 on `/search` → ensure route is defined **before** `app.run(...)`; restart server
* `curl` to `app.github.dev` shows nothing → test via `http://127.0.0.1:8000` inside terminal

---

## 🤖 AI Use & CI Disclosure

* AI helpers: **ChatGPT‑5** (mentor/co‑dev) + optional **GitHub Copilot**
* CI: runs on each push/PR, installs deps, smoke‑tests `import app`

---

**Maintainer:** Aryan Yaghobi
**Mentor / AI Co‑Developer:** ChatGPT‑5

> This README documents Phase 2 completion and provides clear run steps, verification, and a rubric‑aligned roadmap.
