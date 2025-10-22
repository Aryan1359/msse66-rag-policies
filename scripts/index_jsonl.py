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
    files = sorted(list(CORPUS_DIR.glob("*.md")) + list(CORPUS_DIR.glob("*.txt")) + list(CORPUS_DIR.glob("*.pdf")) + list(CORPUS_DIR.glob("*.html")) + list(CORPUS_DIR.glob("*.htm")))
    if not files:
        print(f"[ERROR] No supported files found in {CORPUS_DIR}/", file=sys.stderr)
        sys.exit(1)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    try:
        import PyPDF2
    except ImportError:
        PyPDF2 = None

    with INDEX_PATH.open("w", encoding="utf-8") as f:
        for doc_idx, p in enumerate(files, start=1):
            if p.suffix.lower() == ".pdf":
                if not PyPDF2:
                    print(f"[WARN] Skipping PDF {p} (PyPDF2 not installed)", file=sys.stderr)
                    continue
                try:
                    reader = PyPDF2.PdfReader(str(p))
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception as e:
                    print(f"[ERROR] Failed to extract PDF {p}: {e}", file=sys.stderr)
                    continue
            else:
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
