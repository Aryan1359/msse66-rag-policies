# This file has been replaced with the new implementation.
#!/usr/bin/env python3
import argparse, json, os, sys, time
from statistics import median

# Helper: read JSONL
def read_jsonl(path, limit=None):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip():
                items.append(json.loads(line))
            if limit is not None and len(items) >= limit:
                break
    return items

# Helper: percentile without numpy (linear interpolation of ranks)
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

# Tiny HTTP client calling local Flask app if available; otherwise import test client
def ask(question):
    # Strategy 1: in-process test client
    try:
        import sys, os
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/..")
        import app as app_module
        app = app_module.app
        with app.test_client() as client:
            t0 = time.time()
            resp = client.post("/ask", json={"q": question})
            dt_ms = int((time.time() - t0) * 1000)
            data = resp.get_json(force=True)
            return data, dt_ms
    except Exception:
        # Strategy 2: fallback to HTTP localhost if app is running
        try:
            import urllib.request
            import urllib.error
            import urllib.parse
            t0 = time.time()
            req = urllib.request.Request(
                "http://127.0.0.1:8000/ask",
                data=json.dumps({"q": question}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = r.read()
            dt_ms = int((time.time() - t0) * 1000)
            data = json.loads(payload.decode("utf-8"))
            return data, dt_ms
        except Exception as e:
            raise RuntimeError(f"/ask call failed: {e}")

def bool_grounded(answer_dict):
    # Heuristic: consider grounded if citations list exists and has at least one item
    cites = (answer_dict or {}).get("citations") or (answer_dict or {}).get("sources")
    return bool(cites) and len(cites) > 0

def bool_citation_accuracy(answer_dict):
    """
    Heuristic: if answer_dict has 'citations' with pairs (doc_id, chunk_id) or strings referencing known ids,
    and 'retrieved' or 'sources' list contains those ids, we count it as accurate (at least one match).
    Adjust to whatever structure /ask returns (keep permissive).
    """
    if not answer_dict:
        return False
    cited = answer_dict.get("citations") or answer_dict.get("sources") or []
    retrieved = answer_dict.get("retrieved") or answer_dict.get("sources") or []
    # Normalize to strings like "doc_id:chunk_id" or dicts with doc_id/chunk_id
    def norm(x):
        if isinstance(x, dict):
            did = x.get("doc_id") or x.get("id") or x.get("doc")
            cid = x.get("chunk_id") or x.get("chunk")
            return f"{did}:{cid}" if (did is not None and cid is not None) else str(did or x)
        return str(x)
    cited_norm = set(norm(x) for x in cited)
    retr_norm = set(norm(x) for x in retrieved)
    # If retrieval returns only doc ids and citations include chunk ids, fall back to doc id match
    def doc_only(s):
        return set(i.split(":")[0] if ":" in i else i for i in s)
    return len(cited_norm & retr_norm) > 0 or len(doc_only(cited_norm) & doc_only(retr_norm)) > 0

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

    results = []
    total_ms = []
    grounded_count = 0
    citation_ok_count = 0

    for item in qa:
        qid = item.get("id")
        q = item.get("question")
        data, dt = ask(q)
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
        "min_grounded": args["min_grounded"] if isinstance(args, dict) else args.min_grounded,
        "min_citation": args["min_citation"] if isinstance(args, dict) else args.min_citation,
        "p95_total_budget_ms": args["p95_total"] if isinstance(args, dict) else args.p95_total,
        "pass_grounded": grounded_rate >= args.min_grounded,
        "pass_citation": citation_rate >= args.min_citation,
        "pass_p95": p95 <= args.p95_total,
    }

    os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    # Markdown report
    md = []
    md.append("# Evaluation Summary\n")
    md.append(f"- Items: **{n}**")
    md.append(f"- Grounded rate: **{grounded_rate:.2%}** (threshold {args.min_grounded:.0%})")
    md.append(f"- Citation accuracy: **{citation_rate:.2%}** (threshold {args.min_citation:.0%})")
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

    # Gate: exit code 2 on any failure
    if not (summary["pass_grounded"] and summary["pass_citation"] and summary["pass_p95"]):
        print("CI GATE FAILED. See report.", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
import requests, json, time, re, argparse
import sys, os
import sys

def load_qa(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", type=str, default="http://127.0.0.1:8000")
    ap.add_argument("--file", type=str, default="data/eval/qa.jsonl")
    ap.add_argument("--topk", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--inproc", action="store_true", help="Run evaluation in-process using Flask test client")
    args = ap.parse_args()
    qa = load_qa(args.file)
    rows = []
    if args.inproc:
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/..")
        import app as app_module
        client = app_module.app.test_client()
        def ask_fn(question, topk):
            r = client.post("/ask", json={"question": question, "topk": topk})
            return r.get_json()
    else:
        def ask_fn(question, topk):
            r = requests.post(f"{args.server}/ask", json={"question": question, "topk": topk}, timeout=args.timeout)
            return r.json()
    for item in qa:
        qid = item["id"]
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        t0 = time.time()
        try:
            data = ask_fn(question, args.topk)
            elapsed = int((time.time() - t0) * 1000)
        except Exception as ex:
            rows.append({"id": qid, "error": str(ex)})
            continue
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        source_labels = data.get("source_labels", {})
        retrieval_ms = data.get("retrieval_ms", 0)
        llm_ms = data.get("llm_ms", 0)
        has_sources = len(sources) > 0
        citation_present = bool(re.search(r"\[S\d+\]", answer))
        citation_correct = (not citation_present) or (citation_present and has_sources)
        keyword_hit = any(kw.lower() in answer.lower() for kw in expected_keywords)
        rows.append({
            "id": qid,
            "has_sources": has_sources,
            "citation_present": citation_present,
            "citation_correct": citation_correct,
            "keyword_hit": keyword_hit,
            "retrieval_ms": retrieval_ms,
            "llm_ms": llm_ms,
            "total_ms": elapsed,
            "answer": answer,
            "sources": sources,
            "source_labels": source_labels
        })
    # Aggregates
    n = len(rows)
    summary = {
        "n": n,
        "grounded_rate": sum(r.get("has_sources", False) for r in rows) / n if n else 0,
        "citation_rate": sum(r.get("citation_present", False) for r in rows) / n if n else 0,
        "citation_correct_rate": sum(r.get("citation_correct", False) for r in rows) / n if n else 0,
        "keyword_hit_rate": sum(r.get("keyword_hit", False) for r in rows) / n if n else 0,
        "mean_retrieval_ms": int(sum(r.get("retrieval_ms", 0) for r in rows) / n) if n else 0,
        "mean_llm_ms": int(sum(r.get("llm_ms", 0) for r in rows) / n) if n else 0,
        "mean_total_ms": int(sum(r.get("total_ms", 0) for r in rows) / n) if n else 0,
    }
    out = {"rows": rows, "summary": summary}
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
