
#!/usr/bin/env python3
import json, argparse, sys
from pathlib import Path

def run_search(query, base_url, mode, topk):
    try:
        import requests, time
    except ImportError:
        print("[ERR] 'requests' not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    t0 = time.perf_counter()
    r = requests.get(f"{base_url}/search", params={"q": query, "mode": mode, "topk": topk}, timeout=10)
    t1 = time.perf_counter()
    data = r.json()
    doc_ids = [s.get("doc_id") for s in data.get("sources", []) if s.get("doc_id")]
    elapsed_ms = (t1 - t0) * 1000.0
    return doc_ids, elapsed_ms

def main():
    parser = argparse.ArgumentParser(description="Tiny eval single-item HTTP check")
    parser.add_argument("--qa", default="data/eval/qa_sample.json", help="Path to eval set")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Flask base URL")
    parser.add_argument("--mode", default="keyword", choices=["keyword","vector"], help="retrieval mode")
    parser.add_argument("--topk", type=int, default=3, help="top-k")
    args = parser.parse_args()

    qa_path = Path(args.qa)
    if not qa_path.exists():
        print(f"[ERR] Eval file not found: {qa_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(qa_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        print("[ERR] Eval file must be a non-empty JSON array", file=sys.stderr)
        sys.exit(1)

    import statistics
    hits = 0
    total = len(data)
    latencies = []
    for item in data:
        qid = item.get("id")
        question = item.get("question")
        expected_doc_ids = item.get("expected_doc_ids", [])
        print(f"[Q] {question}")

        doc_ids, latency_ms = run_search(question, args.base_url, args.mode, args.topk)
        latencies.append(latency_ms)
        print(f"[sources.doc_ids] {doc_ids}")
        print(f"[latency_ms] {latency_ms:.2f}")

        overlap = bool(set(doc_ids) & set(expected_doc_ids))
        print(f"[overlap] {overlap}")
        if overlap:
            hits += 1

    percent = (hits / total) * 100 if total else 0
    print(f"[summary] hits={hits}/{total} ({percent:.0f}%)")

    if latencies:
        min_ms = min(latencies)
        avg_ms = statistics.mean(latencies)
        p50_ms = statistics.median(latencies)
        p95_ms = max(latencies)  # for N<20, use max as p95~
        print(f"[latency] min={min_ms:.2f}ms p50={p50_ms:.2f}ms avg={avg_ms:.2f}ms p95~={p95_ms:.2f}ms")

if __name__ == "__main__":
    main()
