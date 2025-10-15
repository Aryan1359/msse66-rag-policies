#!/usr/bin/env python3
"""
Tiny ingestion loader: reads Markdown files from data/policies/ and prints basic stats.
No external deps; safe for CI.
"""
from pathlib import Path
import re
import sys

CORPUS_DIR = Path("data/policies")

def file_stats(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    chars = len(text)
    words = len(re.findall(r"\b\w+\b", text))
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    headings = len(re.findall(r"^#{1,6}\s", text, flags=re.M))
    return {"name": path.name, "chars": chars, "words": words, "lines": lines, "headings": headings}

def main():
    if not CORPUS_DIR.exists():
        print(f"[ERROR] Corpus folder not found: {CORPUS_DIR.resolve()}", file=sys.stderr)
        sys.exit(1)

    files = sorted(CORPUS_DIR.glob("*.md"))
    if not files:
        print(f"[WARN] No .md files found in {CORPUS_DIR}/")
        sys.exit(0)

    print(f"Found {len(files)} file(s) in {CORPUS_DIR}/\n")
    total_words = 0
    for p in files:
        s = file_stats(p)
        total_words += s["words"]
        print(f"- {s['name']}: {s['words']} words, {s['lines']} lines, {s['headings']} headings, {s['chars']} chars")

    print(f"\nTOTAL words: {total_words}")
    print("\nPreview (first 120 chars of first file):")
    preview = files[0].read_text(encoding="utf-8", errors="replace")[:120].replace("\n", " ")
    print(preview)

if __name__ == "__main__":
    main()
