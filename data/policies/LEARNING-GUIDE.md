# MSSE66+ Learning Guide — RAG on Company Policies

This guide provides a structured path for developing and understanding the **RAG (Retrieval-Augmented Generation)** system for company policy Q&A, phase by phase.

---

## 📘 Overview

The goal is to learn practical **AI Engineering for RAG systems** using local tools (Flask + Python + lightweight search). Each phase builds a deeper understanding of search, embeddings, retrieval, and evaluation.

Repo: [https://github.com/Aryan1359/msse66-rag-policies](https://github.com/Aryan1359/msse66-rag-policies)

---

## 🧩 Phase 1 — Foundation Setup

**Goal:** Create a minimal working environment.

**Key Skills:**

* Virtual environments (`.venv`)
* Python version pinning
* Basic Flask API structure
* Health check endpoints

**Deliverables:**

* `app.py` with `/` and `/health`
* `.venv`, `.python-version`, and `.env` setup

**Verification:**

```bash
curl http://127.0.0.1:8000/health
```

Should return `{"status": "ok"}`.

---

## 🧮 Phase 2 — Ingestion & Keyword Search

**Goal:** Build a searchable corpus of policy documents.

**Key Skills:**

* Markdown ingestion and cleaning
* Chunking strategy (overlapping windows)
* JSONL index creation
* Simple keyword retrieval

**Deliverables:**

* `data/policies/*.md`
* `scripts/ingest.py`, `chunk.py`, `index_jsonl.py`, `search_jsonl.py`
* `/search?q=...` API returning top-k results

**Verification:**

```bash
curl "http://127.0.0.1:8000/search?q=vacation%20policy&topk=3"
```

Should return matching chunks with metadata.

---

## 🧠 Phase 3 — Embeddings & Vector Search (Current Phase)

**Goal:** Replace keyword search with semantic search.

**Concepts:**

* Sentence embeddings (semantic similarity)
* Vector databases (FAISS, NumPy cosine search)
* Cosine similarity and top-k ranking

**Deliverables:**

1. `scripts/embed_index.py` – create embedding vectors
2. `scripts/vector_search.py` – cosine similarity retriever
3. Extend Flask `/search` → `mode=keyword|vector`

**Learning Tip:** Compare results between keyword and vector modes to observe semantic retrieval differences.

---

## 📊 Phase 4 — Answer Synthesis

**Goal:** Generate natural-language answers grounded in retrieved chunks.

**Concepts:**

* Prompt construction for LLMs
* Context window management
* Citation grounding

**Deliverables:**

* `scripts/generate_answer.py`
* Flask endpoint `/ask?q=...` using RAG pipeline

**Verification:**
Ask a question and confirm cited chunks align with source text.

---

## 🧪 Phase 5 — Evaluation & Metrics

**Goal:** Assess model quality and retrieval performance.

**Metrics:**

* Groundedness (citation present)
* Citation correctness (text support)
* Latency (ms per query)

**Deliverables:**

* `scripts/evaluate.py`
* Add CI job to auto-run Q&A evaluation

---

## ☁️ Phase 6 — Deployment

**Goal:** Deploy and test the RAG app in production.

**Concepts:**

* Render.com or Vercel free tier
* CI/CD pipeline with smoke tests
* Environment variables in hosted app

**Deliverables:**

* Deployed RAG endpoint
* Updated README with usage guide

---

## 📚 Reference Learning Resources

* [Sentence-Transformers Docs](https://www.sbert.net/)
* [FAISS GitHub](https://github.com/facebookresearch/faiss)
* [Flask Documentation](https://flask.palletsprojects.com/)
* [OpenAI Embedding API](https://platform.openai.com/docs/guides/embeddings)

---

**Maintainer:** Aryan Yaghobi
**Mentor:** ChatGPT-5
