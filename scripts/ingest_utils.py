import os
import json
import csv
from datetime import datetime
from typing import List
from pdfminer.high_level import extract_text
from bs4 import BeautifulSoup

POLICIES_DIR = os.path.join("data", "policies")
PARSED_DIR = os.path.join("data", "parsed")
PARSE_LOG = os.path.join("logs", "parse.jsonl")
CLEAN_LOG = os.path.join("logs", "clean.jsonl")
PARSED_STATS_CSV = os.path.join("data", "index", "parsed_stats.csv")

# List uploaded files
def list_uploaded_files(base_dir=POLICIES_DIR) -> List[dict]:
    files = []
    for fname in os.listdir(base_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext in {".md", ".txt", ".pdf", ".html", ".htm"}:
            files.append({
                "doc_id": fname,
                "ext": ext,
                "path": os.path.join(base_dir, fname)
            })
    return files

# Parse a file
def parse_file(path: str) -> dict:
    doc_id = os.path.basename(path)
    ext = os.path.splitext(doc_id)[1].lower()
    out_path = os.path.join(PARSED_DIR, doc_id + ".txt")
    os.makedirs(PARSED_DIR, exist_ok=True)
    result = {"doc_id": doc_id, "ext": ext, "status": "error", "chars": 0, "words": 0, "text_path": out_path, "error": None, "ts": datetime.utcnow().isoformat()}
    try:
        if ext == ".pdf":
            text = extract_text(path)
        elif ext in {".html", ".htm"}:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "lxml")
                for tag in soup(["script", "style"]): tag.decompose()
                text = soup.get_text(separator="\n")
        elif ext in {".md", ".txt"}:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            raise Exception("Unsupported file type")
        # Normalize whitespace
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        result["chars"] = len(text)
        result["words"] = len(text.split())
        result["status"] = "parsed"
    except Exception as e:
        result["error"] = str(e)
    # Log
    os.makedirs(os.path.dirname(PARSE_LOG), exist_ok=True)
    with open(PARSE_LOG, "a", encoding="utf-8") as logf:
        logf.write(json.dumps(result) + "\n")
    return result

# Clean a parsed text file
def clean_text_file(parsed_path: str) -> dict:
    doc_id = os.path.basename(parsed_path).replace(".txt", "")
    cleaned_path = parsed_path  # Overwrite for simplicity
    result = {"doc_id": doc_id, "status": "error", "chars": 0, "words": 0, "cleaned_path": cleaned_path, "error": None, "ts": datetime.utcnow().isoformat()}
    try:
        with open(parsed_path, "r", encoding="utf-8") as f:
            text = f.read()
        # Minimal clean: trim double spaces, normalize newlines
        cleaned = ' '.join(text.split())
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        with open(cleaned_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        result["chars"] = len(cleaned)
        result["words"] = len(cleaned.split())
        result["status"] = "cleaned"
    except Exception as e:
        result["error"] = str(e)
    # Log
    os.makedirs(os.path.dirname(CLEAN_LOG), exist_ok=True)
    with open(CLEAN_LOG, "a", encoding="utf-8") as logf:
        logf.write(json.dumps(result) + "\n")
    return result

# Update parsed stats CSV
def update_parsed_stats(doc_id, ext, status, chars, words, last_parsed_iso):
    os.makedirs(os.path.dirname(PARSED_STATS_CSV), exist_ok=True)
    stats = get_parsed_stats()
    found = False
    for row in stats:
        if row["doc_id"] == doc_id:
            row.update({"ext": ext, "status": status, "chars": chars, "words": words, "last_parsed_iso": last_parsed_iso})
            found = True
    if not found:
        stats.append({"doc_id": doc_id, "ext": ext, "status": status, "chars": chars, "words": words, "last_parsed_iso": last_parsed_iso})
    with open(PARSED_STATS_CSV, "w", encoding="utf-8", newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=["doc_id", "ext", "status", "chars", "words", "last_parsed_iso"])
        writer.writeheader()
        writer.writerows(stats)

# Get parsed stats for table
def get_parsed_stats() -> List[dict]:
    stats = []
    if os.path.exists(PARSED_STATS_CSV):
        with open(PARSED_STATS_CSV, "r", encoding="utf-8") as csvf:
            reader = csv.DictReader(csvf)
            for row in reader:
                stats.append(row)
    return stats
