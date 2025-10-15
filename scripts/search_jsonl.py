#!/usr/bin/env python3
"""
Keyword search over JSONL index (no external deps).

Usage:
  python scripts/search_jsonl.py "pto policy" --topk 3
"""
from pathlib import Path
import argparse
import json
import re
from typing import List, Dict

INDEX_PATH = Path("data/index/policies.jsonl")

def load_index(path: Path) -> List[Dict]:
    recs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            recs.append(json.loads(line))
    return recs

def score(text: str, terms: List[str]) -> int:
    # Simple case-insensitive term frequency with word-boundaries
    s = 0
    for t in terms:
        if not t:
            continue
        s += len(re.findall(rf"\b{re.escape(t)}\b", text, flags=re.I))
    return s

def search(recs: List[Dict], query: str, topk: int = 3) -> List[Dict]:
    terms = [t.strip() for t in query.split() if t.strip()]
    scored = []
    for r in recs:
        sc = score(r["text"], terms)
        if sc > 0:
            scored.append((sc, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:topk]]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="search terms, e.g., 'pto accrual'")
    ap.add_argument("--topk", type=int, default=3, help="number of results")
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        print(f"[ERROR] Index file not found at {INDEX_PATH}. Run scripts/index_jsonl.py first.")
        raise SystemExit(1)

    recs = load_index(INDEX_PATH)
    hits = search(recs, args.query, topk=args.topk)

    if not hits:
        print("No results.")
        return

    print(f"Top {len(hits)} results for: \"{args.query}\"")
    for i, h in enumerate(hits, start=1):
        preview = re.sub(r"\s+", " ", h["text"])[:160]
        print(f"\n[{i}] {h['id']}  (source: {h['source']}, ~{h['tokens_rough']} tokens)")
        print(f"    {preview}{'...' if len(h['text'])>160 else ''}")

if __name__ == "__main__":
    main()
