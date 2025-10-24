# Design and Evaluation Document

## 1. Design and Architecture Decisions

### Modular, Stepwise Pipeline
- **Decision:** Each pipeline step (upload, parse, chunk, embed, search, ask, evaluate) is implemented as a separate Flask blueprint and UI page.
- **Why:** Maximizes maintainability, clarity, and extensibility. Each step can be developed, tested, and debugged independently.

### Technology Choices
- **Flask:** Lightweight, flexible, and easy to modularize with blueprints.
- **Bootstrap & Lottie:** For a modern, responsive UI with engaging animations.
- **sentence-transformers (MiniLM):** Fast, high-quality embeddings for semantic search.
- **FAISS/NumPy:** Efficient vector search and keyword retrieval.
- **OpenRouter, Groq, OpenAI:** Pluggable LLM providers, with API key management in the UI for flexibility and cost control.
- **Render.com:** Simple, reproducible cloud deployment with persistent storage and free tier support.

### Logging & Metrics
- **Decision:** All user questions, answers, citations, and latency are logged persistently (JSONL files per step).
- **Why:** Enables robust evaluation, debugging, and reproducibility. Metrics dashboard (Step 8) provides real-time feedback on system performance.

### Provider & Chunking Selection
- **Decision:** Users can select LLM provider and chunking method in the UI.
- **Why:** Supports experimentation and benchmarking of different retrieval and generation strategies.

### API-First Design
- **Decision:** All core functionality is exposed via REST endpoints (`/search`, `/ask`, `/health`).
- **Why:** Enables easy integration, automation, and CI-based evaluation.

---

## 2. Evaluation Approach and Results

### Evaluation Approach
- **Automated Metrics:**
  - **Groundedness:** % of answers returning a non-empty `sources[]`.
  - **Citation Accuracy:** At least one cited source matches returned sources (heuristic).
  - **Latency:** End-to-end time (p50, p95 in ms).
- **Manual Review:**
  - Sample questions/answers table in Step 7 for human evaluation.
- **CI Gate:**
  - Automated script (`scripts/eval_ask.py`) runs on every push, enforcing thresholds for groundedness, citation, and latency. CI fails if any metric is below threshold.

### Results (as of v0.7.1)
- **Groundedness:** 100% (all answers cite at least one source)
- **Citation Accuracy:** 100% (all citations match expected sources in sample set)
- **Latency:** p95 < 10 ms (extractive mode, no LLM)
- **Deployment:** Live demo on Render, metrics dashboard available in-app

---

For more details, see the README and PROGRESS-LOG.
