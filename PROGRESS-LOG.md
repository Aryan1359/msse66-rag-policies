
# PROGRESS LOG — MSSE66 RAG Policies
# ✨ Features at a Glance
* Modular, stepwise Flask blueprints (upload, parse, chunk, embed, search, ask, evaluate)
* Modern, responsive UI (Bootstrap, Lottie animations, sidebar navigation)
* Indexed Files table with delete icons
* Ask a Question box with clear answer and sources formatting
* Fast keyword and vector retrieval
* Grounded answers with citations and robust logging
* Metrics dashboard: grounded rate, citation correctness, latency, recent questions
* Automated evaluation & CI gate (groundedness, citation, latency)
* One-click deploy on Render (Procfile, gunicorn, render.yaml)
* Extractive summary (LLM disabled by default, provider-agnostic)
* All steps and logs are reproducible and persistent

## ✅ Phase 1 — Environment & CI Setup

**2025-10-12 → Step 1–7**

| Step | Action                                                  | Result                       |
| :--: | :------------------------------------------------------ | :--------------------------- |
|   1  | Created public repo + Codespaces                        | reproducible cloud dev setup |
|   2  | Virtual environment (`python -m venv .venv`)            | isolated deps                |
|   3  | Pinned Python 3.12.1 (`.python-version`, `runtime.txt`) | consistent runtime           |
|   4  | Added minimal deps (`Flask`, `python-dotenv`)           | base framework               |
|   5  | Minimal Flask app (`/`, `/health`)                      | returns `{status:ok}`        |
|   6  | Branch → PR → merge workflow                            | clean main history           |
|   7  | CI pipeline (`.github/workflows/ci.yml`)                | smoke-import test green ✅    |

---

## ✅ Phase 2 — Ingestion & Keyword Retrieval

* Implemented `scripts/ingest.py`, `scripts/chunk.py`, and `scripts/index_jsonl.py`.
* Added sample markdown policies under `data/policies/`.
* `/search` endpoint returns keyword matches with `mode`, `query`, `topk`, `results[]`.
* CI + local verification complete.

---

## ✅ Phase 3 — Embeddings & Vector Search

* Added `scripts/embed_index.py` + `scripts/vector_search.py` (NumPy cosine).
* Extended `/search` to support `mode=vector`.
* Added `sources[]` array for compact citation info.
* Seeded small evaluation QA set in `data/eval/`.
* CI smoke tests green.

---

## ✅ Phase 4 — UI & Answer Formatting (2025-10-21)

* Homepage UI redesigned for clarity and organization
* Indexed Files now shown in a table with delete icons
* Ask a Question box displays answer first, sources below
* All changes deployed and live on Render

---

## ✅ Phase 4 — RAG Answer Synthesis

**2025-10-20**

* **Step 1:** Created `feat/phase4-llm-setup` branch — scaffolded `scripts/llm_client.py` with safe fallback, CI-ready.
* **Step 2:** Added `scripts/generate_answer.py` (retrieval → prompt → LLM), fallback, CLI test, docs.

  ```bash
  python -m scripts.generate_answer --q "PTO accrual policy?" --topk 3
  ```
* **Step 3:** Implemented `/ask` endpoint (POST + GET) wrapping generator, returning `answer`, `sources`, `source_labels`, timing fields.

  ```bash
  curl -s -X POST http://127.0.0.1:8000/ask \
    -H "Content-Type: application/json" \
    -d '{"question":"How do holidays accrue?","topk":4}' | jq
  ```
* **Step 4:** Citation polish `[S#]` ↔ `source_labels` mapping validated.

  ```python
  def test_citations_map():
      import app, json
      c = app.app.test_client()
      r = c.post("/ask", json={"question":"PTO accrual policy?","topk":3})
      assert r.status_code == 200
      data = r.get_json()
      k = len(data["sources"])
      assert list(data["source_labels"].keys()) == [f"S{i}" for i in range(1, k+1)]
  ```

---

## ✅ Phase 5 — Evaluation Thresholds & CI Gate

**2025-10-21**

* Created `scripts/eval_ask.py` — computes groundedness, citation rate, p95 latency without NumPy.
* Added Makefile target `eval-gate` with thresholds + artifact outputs.
* Expanded QA set to ≈ 15 diverse policy questions.
* CI gate fails (exit 2) if any metric below thresholds.
* Workflow `.github/workflows/eval.yml` uploads artifacts + enforces gate.
* Verified locally: 100 % grounded/cited, p95 ≈ 8 ms < 4 000 ms ✅
* Merged PR #17 → tagged **v0.6.0**.

---

## ✅ Phase 6 — Deployment Scaffold (Render)

**2025-10-21 → v0.7.0–v0.7.1**

* Added `gunicorn` to `requirements.txt`.
* Added `Procfile` (`web: gunicorn app:app --bind 0.0.0.0:${PORT}`).
* Added `render/render.yaml` (free plan, health /health).
* Verified local gunicorn run + CI green.
* Deployed to **Render** successfully → [https://msse66-rag-policies.onrender.com](https://msse66-rag-policies.onrender.com) ✅
* Live Demo: [https://msse66-rag-policies.onrender.com](https://msse66-rag-policies.onrender.com)
* Updated README with **Live Demo** section.
* Merged PR #19 → tagged **v0.7.1**.

---

## ✅ Phase 7 — Modularization, Logging, and Metrics (2025-10-22 to 2025-10-24)

* Refactored app into modular blueprints: each pipeline step (upload, parse, chunk, embed, search, ask, evaluate) is a separate module and UI page.
* Implemented robust, persistent logging for all user questions, answers, citations, and latency (step7/logs/ask.jsonl, step6/logs/search.jsonl).
* Added metrics dashboard (Step 8): grounded rate, citation correctness, latency, recent questions, and evaluation summary.
* Improved citation extraction and latency logging for accurate metrics.
* UI/UX improvements: navigation bar fixes, homepage redesign with Lottie animation, footer enhancements, better spacing.
* Provider and chunking method selection in Step 7 UI.
* API key management in UI for OpenRouter, Groq, OpenAI.
* Persistent log and data file handling for Render deployment.
* Merged feature branches, resolved conflicts, and cleaned up old branches.
* Rewrote and updated README (structure, usage, deployment, API, evaluation).
* Added deployed.md with live demo link as required.
* All changes tested and validated in production.

---

## 🔮 Next Steps (Future Phases)

| Phase | Goal                                         | Status     |
| :---- | :------------------------------------------- | :--------- |
| 7     | Default vector mode /search & /ask           | pending    |
| 8     | Optional LLM answer mode (`ANSWER_MODE=llm`) | scaffolded |
| 9     | Evaluator Rubric appendix in README          | planned    |

---

## 🧾 Summary of Tags

| Tag    | Description                     |
| :----- | :------------------------------ |
| v0.4.0 | RAG synthesis scaffold          |
| v0.5.0 | Eval hook for `/ask`            |
| v0.6.0 | Evaluation thresholds + CI gate |
| v0.7.0 | Render deployment scaffold      |
| v0.7.1 | Live Demo URL + docs refresh    |

---

**Maintainer:** [Aryan Yaghobi](https://github.com/Aryan1359)

---

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
