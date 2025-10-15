#!/usr/bin/env python3
"""
JSONL indexer:
- Reads Markdown files from data/policies/
- Splits into overlapping chunks using scripts/chunk.py functions
- Writes JSON Lines to data/index/policies.jsonl
No external dependencies.
"""
from pathlib import Path
import json
import re
import sys

# Reuse chunking logic by importing from scripts/chunk.py
# (Both files live in scripts/, so we can import relatively by adding to sys.path)
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))  # allow "import chunk"

import chunk  # type: ignore

CORPUS_DIR = PROJECT_ROOT / "data" / "policies"
INDEX_PATH = PROJECT_ROOT / "data" / "index" / "policies.jsonl"

def rough_token_count(text: str) -> int:
    # Very rough token proxy: split on word boundaries
    return len(re.findall(r"\b\w+\b", text))

def main():
    files = sorted(CORPUS_DIR.glob("*.md"))
    if not files:
        print(f"[ERROR] No Markdown files found in {CORPUS_DIR}/", file=sys.stderr)
        sys.exit(1)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with INDEX_PATH.open("w", encoding="utf-8") as f:
        for doc_idx, p in enumerate(files, start=1):
            text = p.read_text(encoding="utf-8", errors="replace")
            chunks = chunk.split_with_overlap(text, max_chars=600, overlap=100)
            for i, ch in enumerate(chunks, start=1):
                rec = {
                    "id": f"{p.stem}::chunk-{i}",
                    "doc_id": p.stem,
                    "chunk_id": i,
                    "source": str(p),
                    "text": ch,
                    "chars": len(ch),
                    "tokens_rough": rough_token_count(ch),
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                written += 1

    print(f"Wrote {written} chunk record(s) to {INDEX_PATH}")

if __name__ == "__main__":
    main()
