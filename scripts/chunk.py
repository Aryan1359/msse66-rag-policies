#!/usr/bin/env python3
"""
Simple Markdown chunker with no external deps.

- Loads all *.md from data/policies/
- Splits each file into chunks of ~max_chars with overlap
- Prefers to break on blank lines or headings
- Prints a brief report and sample chunks
"""
from pathlib import Path
import re
from typing import List

CORPUS_DIR = Path("data/policies")

def split_with_overlap(text: str, max_chars: int = 600, overlap: int = 100) -> List[str]:
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Candidate split points: blank lines or headings
    boundaries = [0]
    for m in re.finditer(r"(?m)^(?:\s*$|#{1,6}\s.*$)", text):
        boundaries.append(m.start())
    boundaries.append(len(text))
    boundaries = sorted(set(boundaries))

    chunks = []
    i = 0
    while i < len(text):
        target_end = min(i + max_chars, len(text))

        # Find the last boundary before or at target_end (but after i)
        cut = None
        for b in boundaries:
            if i < b <= target_end:
                cut = b
        if cut is None or cut - i < max_chars * 0.3:
            # Fallback: hard cut
            cut = target_end

        chunk = text[i:cut].strip()
        if chunk:
            chunks.append(chunk)

        if cut >= len(text):
            break

        # Advance with overlap
        i = max(0, cut - overlap)

        # Avoid infinite loop if overlap is too large and nothing advances
        if i >= cut:
            i = cut

    return chunks

def chunk_file(path: Path, max_chars: int = 600, overlap: int = 100) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return split_with_overlap(text, max_chars=max_chars, overlap=overlap)

def main():
    files = sorted(CORPUS_DIR.glob("*.md"))
    if not files:
        print(f"[WARN] No Markdown files in {CORPUS_DIR}/")
        return

    total_chunks = 0
    for p in files:
        chunks = chunk_file(p)
        total_chunks += len(chunks)
        print(f"{p.name}: {len(chunks)} chunk(s)")
        # Show first chunk preview
        if chunks:
            prev = chunks[0][:140].replace("\n", " ")
            print(f"  - first chunk preview: {prev}{'...' if len(chunks[0])>140 else ''}")

    print(f"\nTOTAL chunks: {total_chunks}")

    # Print a sample chunk (file 1, chunk 2) if available
    if files:
        ex = chunk_file(files[0])
        if len(ex) >= 2:
            print("\nSample (file 1, chunk 2):\n---")
            print(ex[1])
            print("\n---")

if __name__ == "__main__":
    main()
