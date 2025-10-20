#!/usr/bin/env python3
import argparse, json, os, sys, time
from pathlib import Path

# Ensure repo root on sys.path for `import app`
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def read_jsonl(path, limit=None):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
            if limit is not None and len(items) >= limit:
                break
    return items

def percentile(values, p):
    if not values:
        return 0.0
    x = sorted(values)
    k = (len(x) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(x) - 1)
    if f == c:
        return float(x[int(k)])
    d0 = x[f] * (c - k)
    d1 = x[c] * (k - f)
    return float(d0 + d1)

def ask(question: str):
    """Prefer in-process Flask test client. Fallback to localhost HTTP."""
    # In-process
    try:
        import app as app_module
        app = getattr(app_module, "app", None)
        if app is None:
            create_app = getattr(app_module, "create_app", None)
            if create_app:
                app = create_app()
        if app is None:
            raise RuntimeError("Could not locate Flask `app` or `create_app()`")
        with app.test_client() as client:
            t0 = time.time()
            resp = client.post("/ask", json={"question": question})
            dt_ms = int((time.time() - t0) * 1000)
            data = resp.get_json(force=True)
            return data, dt_ms
    except Exception:
        # Fallback to HTTP if a dev server is already running locally
        import urllib.request, urllib.error
        t0 = time.time()
        req = urllib.request.Request(
            "http://127.0.0.1:8000/ask",
            data=json.dumps({"question": question}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = r.read()
        dt_ms = int((time.time() - t0) * 1000)
        data = json.loads(payload.decode("utf-8"))
        return data, dt_ms

def bool_grounded(answer_dict):
    # Your /ask returns `sources: list[...]` when grounded
    if not isinstance(answer_dict, dict):
        return False
    sources = answer_dict.get("sources") or []
    try:
        return len(sources) > 0
    except TypeError:
        return False

def bool_citation_accuracy(answer_dict):
    # For now: if we have non-empty `sources`, count as citation-ok.
    # (We can tighten later using source_labels/doc_ids.)
    return bool_grounded(answer_dict)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", default="data/eval/qa.jsonl")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--min-grounded", type=float, default=0.75)
    ap.add_argument("--min-citation", type=float, default=0.75)
    ap.add_argument("--p95-total", type=int, default=4000, help="p95 total latency (ms) upper bound")
    ap.add_argument("--json-out", default="data/eval/latest_metrics.json")
    ap.add_argument("--md-out", default="data/eval/latest_metrics.md")
    args = ap.parse_args()

    qa = read_jsonl(args.qa, limit=args.limit)
    if not qa:
        print(f"No eval items found in {args.qa}", file=sys.stderr)
        sys.exit(1)

    results, total_ms = [], []
    grounded_count = citation_ok_count = 0

    for item in qa:
        qid = item.get("id")
        q = item.get("question")
        try:
            data, dt = ask(q)
        except Exception as e:
            data, dt = {"error": str(e)}, 0
        total_ms.append(dt)

        grounded = bool_grounded(data)
        citation_ok = bool_citation_accuracy(data)
        grounded_count += 1 if grounded else 0
        citation_ok_count += 1 if citation_ok else 0

        results.append({
            "id": qid, "q": q, "total_ms": dt,
            "grounded": grounded, "citation_ok": citation_ok,
            "raw": data
        })

    n = len(results)
    p50 = percentile(total_ms, 50)
    p95 = percentile(total_ms, 95)
    grounded_rate = grounded_count / n if n else 0.0
    citation_rate = citation_ok_count / n if n else 0.0

    summary = {
        "n": n,
        "p50_total_ms": p50,
        "p95_total_ms": p95,
        "grounded_rate": grounded_rate,
        "citation_rate": citation_rate,
        "min_grounded": args.min_grounded,
        "min_citation": args.min_citation,
        "p95_total_budget_ms": args.p95_total,
        "pass_grounded": grounded_rate >= args.min_grounded,
        "pass_citation": citation_rate >= args.min_citation,
        "pass_p95": p95 <= args.p95_total,
    }

    os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    md = []
    md.append("# Evaluation Summary\n")
    md.append(f"- Items: **{n}**")
    md.append(f"- Grounded rate: **{grounded_rate:.2%}** (threshold {int(args.min_grounded*100)}%)")
    md.append(f"- Citation accuracy: **{citation_rate:.2%}** (threshold {int(args.min_citation*100)}%)")
    md.append(f"- Latency p50: **{int(p50)} ms**")
    md.append(f"- Latency p95: **{int(p95)} ms** (budget {args.p95_total} ms)")
    md.append("\n## Pass/Fail\n")
    md.append(f"- Grounded: {'✅' if summary['pass_grounded'] else '❌'}")
    md.append(f"- Citation: {'✅' if summary['pass_citation'] else '❌'}")
    md.append(f"- p95 Latency: {'✅' if summary['pass_p95'] else '❌'}")
    md.append("\n## Per-item timings (ms)\n")
    for r in results:
        md.append(f"- {r['id']}: {r['total_ms']} ms | grounded={r['grounded']} | citation_ok={r['citation_ok']}")
    with open(args.md_out, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    # Exit code 2 on any failure
    if not (summary["pass_grounded"] and summary["pass_citation"] and summary["pass_p95"]):
        print("CI GATE FAILED. See report.", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
