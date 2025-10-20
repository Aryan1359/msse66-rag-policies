# 2025-10-20: Phase 4 Step 2 — Added scripts/generate_answer.py (retrieval→prompt→LLM), fallback, CLI, test, docs, PR opened.
  - Branch: feat/phase4-generator
  - CLI example:
    ```bash
    python -m scripts.generate_answer --q "PTO accrual policy?" --topk 3
    # Output: {"question":..., "answer":..., "sources":..., "model":..., ...}
    ```

# 2025-10-20: Phase 4 Step 3 — Implemented /ask endpoint (POST+GET), wraps RAG generator, returns answer, sources, timings, and source_labels. Tested with curl and Flask client.
  - Branch: feat/phase4-generator
  - Example:
    ```bash
    curl -s -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"How do holidays accrue?","topk":4}' | jq
    # Output: {"question":..., "answer":..., "sources":..., "source_labels":..., ...}
    ```

# 2025-10-20: Phase 4 Step 4 — Citation polish: [S#] ↔ source_labels mapping, test passing.
  - Branch: feat/phase4-generator
  - Test:
    ```python
    import app, json
    def test_citations_map():
        c = app.app.test_client()
        r = c.post("/ask", json={"question":"PTO accrual policy?", "topk":3})
        assert r.status_code == 200
        data = r.get_json()
        assert "sources" in data and "source_labels" in data
        k = len(data["sources"])
        assert list(data["source_labels"].keys()) == [f"S{i}" for i in range(1, k+1)]
    ```
- 2025-10-20: Phase 4 Step 3 — Implemented /ask endpoint (POST+GET), wraps RAG generator, returns answer, sources, timings, and source_labels. Tested with curl and Flask client.
# PROGRESS LOG — Steps 1–7

## Step 1: Repo + Codespaces
- Created public repo, opened Codespaces (browser VS Code).
- Why: centralized, reproducible dev without local slowdown.

## Step 2: Virtual Environment
- `python -m venv .venv` + `source .venv/bin/activate`
- Why: isolate dependencies; don’t pollute system Python.

## Step 3: Pin Python + README
- `.python-version` = 3.12.1; `runtime.txt` = python-3.12.1
- README with quickstart.
- Why: reproducible builds on CI and hosting.

## Step 4: Minimal Dependencies
- `requirements.txt` with Flask + python-dotenv; `pip install -r requirements.txt`
- Why: smallest possible working base.

## Step 5: Minimal App
- `app.py` with `/` and `/health`.
- Verified locally in Codespaces; `/health` returned `{"status":"ok"}`.
- Why: foundation for later API endpoints and CI checks.

## Step 6: Branch → PR → Merge
- Worked on `setup/env`, made PR into `main`, merged.
- Why: safe, reviewable history; `main` stays clean.

## Step 7: CI (GitHub Actions)
- `.github/workflows/ci.yml` runs on push/PR:
  - Setup Python, install deps, **import app** (smoke test).
- Why: early detection of breakages.

- 2025-10-19: Added compact `sources[]` to /search responses (feat/search-sources) and merged to main.
- 2025-10-19: Added tiny eval set (5 items) and scripts/eval.py with overlap + latency summary (PR #12).
- 2025-10-20: Phase 4 Step 1 — Created feat/phase4-llm-setup branch, scaffolded Groq LLM client (scripts/llm_client.py), CI-safe fallback, smoke test, docs, PR opened.
- 2025-10-20: Phase 4 Step 2 — Created feat/phase4-generator branch, added scripts/generate_answer.py (retrieval→prompt→LLM), fallback, CLI, test, docs, PR opened. See verification outputs below.
- 2025-10-20: Phase 4 Step 3 — Implemented /ask endpoint (POST+GET), wraps RAG generator, returns answer, sources, timings, and source_labels. Tested with curl and Flask client.
