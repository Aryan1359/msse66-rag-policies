#!/usr/bin/env python3
import json, time, argparse, sys
from pathlib import Path
try:
    import requests  # optional for future HTTP checks
except Exception:
    requests = None

def main():
    parser = argparse.ArgumentParser(description="Tiny eval scaffold")
    parser.add_argument("--qa", default="data/eval/qa_sample.json", help="Path to eval set")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Flask base URL (for future HTTP checks)")
    parser.add_argument("--mode", default="keyword", choices=["keyword","vector"], help="retrieval mode (future)")
    parser.add_argument("--topk", type=int, default=3, help="top-k (future)")
    args = parser.parse_args()

    qa_path = Path(args.qa)
    if not qa_path.exists():
        print(f"[ERR] Eval file not found: {qa_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(qa_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("[ERR] Eval file must be a JSON array", file=sys.stderr)
        sys.exit(1)

    # Timing scaffold
    t0 = time.perf_counter()
    print(f"[INFO] Loaded {len(data)} eval items from {qa_path}")

    # TODO: In next step, call /search and measure latency + overlap
    # For now, just print the questions to confirm wiring.
    for i, item in enumerate(data, 1):
        qid = item.get("id")
        q = item.get("question")
        expected = item.get("expected_doc_ids", [])
        print(f"[ITEM {i}] id={qid} | q={q} | expected_doc_ids={expected}")

    t1 = time.perf_counter()
    print(f"[TIME] total_seconds={(t1 - t0):.4f}")
    print("[NEXT] Implement HTTP calls to /search and compute overlap/latency metrics.")

if __name__ == "__main__":
    main()
