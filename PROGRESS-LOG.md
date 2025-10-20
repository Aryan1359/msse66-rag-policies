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
