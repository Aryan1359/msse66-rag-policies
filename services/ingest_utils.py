
import os
import re
import json
import csv
import unicodedata
from datetime import datetime
from pdfminer.high_level import extract_text
from bs4 import BeautifulSoup
from html import unescape
from typing import List

POLICIES_DIR = os.path.join("steps", "step1", "data-Policies")
PARSED_RAW_DIR = os.path.join("steps", "step2", "Parse-Results")
PARSED_DIR = os.path.join("steps", "step3", "Clean-Results")
PARSED_STATS_CSV = os.path.join("data", "index", "parsed_stats.csv")
PARSE_LOG = os.path.join("logs", "parse.jsonl")
CLEAN_LOG = os.path.join("logs", "clean.jsonl")

# 1. Slugify filename
def slugify(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename))[0]
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", base.lower()).strip("_")
    return slug

# 2. Parse file to raw text
def parse_file(src_path: str) -> dict:
    t0 = datetime.utcnow()
    ext = os.path.splitext(src_path)[1].lower()
    doc_id = slugify(src_path)
    out_path = os.path.join(PARSED_RAW_DIR, f"{doc_id}.txt")
    os.makedirs(PARSED_RAW_DIR, exist_ok=True)
    status = "ok"
    error = None
    text = ""
    bytes_in = 0
    try:
        if ext == ".pdf":
            text = extract_text(src_path)
            if not text.strip():
                status = "no_text"
        elif ext in {".html", ".htm"}:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "lxml")
                for tag in soup(["script", "style"]): tag.decompose()
                text = soup.get_text(separator="\n")
                text = unescape(text)
        elif ext in {".md", ".txt"}:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            status = "error"
            error = f"Unsupported file type: {ext}"
        bytes_in = os.path.getsize(src_path)
        # Normalize newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Write output
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        status = "error"
        error = str(e)
    ms_elapsed = int((datetime.utcnow() - t0).total_seconds() * 1000)
    chars_out = len(text)
    log_entry = {
        "ts": datetime.utcnow().isoformat(),
        "doc_id": doc_id,
        "ext": ext,
        "bytes_in": bytes_in,
        "chars_out": chars_out,
        "ms_elapsed": ms_elapsed,
        "status": status,
        "error": error
    }
    os.makedirs(os.path.dirname(PARSE_LOG), exist_ok=True)
    with open(PARSE_LOG, "a", encoding="utf-8") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    update_parsed_stats(doc_id, ext, bytes_in, chars_out, None, status, datetime.utcnow().isoformat(), error)
    return {
        "status": status,
        "doc_id": doc_id,
        "ext": ext,
        "bytes_in": bytes_in,
        "chars_out": chars_out,
        "parsed_raw_path": out_path,
        "error": error
    }

# 3. Clean parsed text
def clean_text(parsed_raw_path: str) -> dict:
    t0 = datetime.utcnow()
    doc_id = slugify(parsed_raw_path)
    cleaned_path = os.path.join(PARSED_DIR, f"{doc_id}.txt")
    os.makedirs(PARSED_DIR, exist_ok=True)
    status = "ok"
    error = None
    chars_in = 0
    chars_out = 0
    try:
        with open(parsed_raw_path, "r", encoding="utf-8") as f:
            text = f.read()
        chars_in = len(text)
        # Collapse 3+ newlines to max 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Convert tabs to spaces
        text = text.replace("\t", " ")
        # Trim trailing spaces per line
        text = "\n".join([line.rstrip() for line in text.splitlines()])
        # Normalize Unicode (smart quotes, dashes, etc.)
        text = unicodedata.normalize("NFKC", text)
        # Decode HTML entities (if any)
        text = unescape(text)
        # Write output
        with open(cleaned_path, "w", encoding="utf-8") as f:
            f.write(text)
        chars_out = len(text)
    except Exception as e:
        status = "error"
        error = str(e)
    ms_elapsed = int((datetime.utcnow() - t0).total_seconds() * 1000)
    log_entry = {
        "ts": datetime.utcnow().isoformat(),
        "doc_id": doc_id,
        "chars_in": chars_in,
        "chars_out": chars_out,
        "ms_elapsed": ms_elapsed,
        "status": status,
        "error": error
    }
    os.makedirs(os.path.dirname(CLEAN_LOG), exist_ok=True)
    with open(CLEAN_LOG, "a", encoding="utf-8") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    update_parsed_stats(doc_id, None, None, chars_out, None, status, datetime.utcnow().isoformat(), error, chars_in=chars_in)
    return {
        "status": status,
        "doc_id": doc_id,
        "chars_in": chars_in,
        "chars_out": chars_out,
        "cleaned_path": cleaned_path,
        "error": error
    }

# 4. Update parsed stats CSV
def update_parsed_stats(doc_id, ext, bytes_in, chars_raw, chars_clean, status, last_parsed_iso, error, chars_in=None):
    os.makedirs(os.path.dirname(PARSED_STATS_CSV), exist_ok=True)
    stats = get_parsed_stats()
    found = False
    for row in stats:
        if row["doc_id"] == doc_id:
            row.update({
                "ext": ext if ext is not None else row.get("ext"),
                "bytes_in": bytes_in if bytes_in is not None else row.get("bytes_in"),
                "chars_raw": chars_raw if chars_raw is not None else row.get("chars_raw"),
                "chars_clean": chars_clean if chars_clean is not None else row.get("chars_clean"),
                "status": status,
                "last_parsed_iso": last_parsed_iso,
                "error": error
            })
            if chars_in is not None:
                row["chars_in"] = chars_in
            found = True
    if not found:
        stats.append({
            "doc_id": doc_id,
            "ext": ext,
            "bytes_in": bytes_in,
            "chars_raw": chars_raw,
            "chars_clean": chars_clean,
            "status": status,
            "last_parsed_iso": last_parsed_iso,
            "error": error,
            "chars_in": chars_in
        })
    with open(PARSED_STATS_CSV, "w", encoding="utf-8", newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=["doc_id","ext","bytes_in","chars_raw","chars_clean","status","last_parsed_iso","error","chars_in"])
        writer.writeheader()
        writer.writerows(stats)

# 5. Get parsed stats for table
def get_parsed_stats() -> List[dict]:
    stats = []
    if os.path.exists(PARSED_STATS_CSV):
        with open(PARSED_STATS_CSV, "r", encoding="utf-8") as csvf:
            reader = csv.DictReader(csvf)
            for row in reader:
                stats.append(row)
    return stats
