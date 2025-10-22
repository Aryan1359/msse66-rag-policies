# Moved from scripts/ingest_utils.py
import os
import json
import csv
from datetime import datetime
from werkzeug.utils import secure_filename

POLICIES_DIR = os.path.join('data', 'policies')
PARSED_DIR = os.path.join('data', 'parsed')
PARSED_STATS_CSV = os.path.join('data', 'index', 'parsed_stats.csv')
PARSE_LOG = os.path.join('logs', 'parse.jsonl')
CLEAN_LOG = os.path.join('logs', 'clean.jsonl')

# Utility functions

def list_uploaded_files(base_dir=POLICIES_DIR):
    files = []
    for fname in os.listdir(base_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext in {'.md', '.txt', '.pdf', '.html', '.htm'}:
            files.append({
                'doc_id': fname,
                'ext': ext,
                'size': os.path.getsize(os.path.join(base_dir, fname)),
                'path': os.path.join(base_dir, fname)
            })
    return files

def parse_file(path):
    ext = os.path.splitext(path)[1].lower()
    doc_id = os.path.basename(path)
    out_path = os.path.join(PARSED_DIR, doc_id + '.txt')
    result = {'doc_id': doc_id, 'status': 'error', 'chars': 0, 'words': 0, 'ts': None, 'error': None}
    try:
        os.makedirs(PARSED_DIR, exist_ok=True)
        if not os.path.exists(path):
            raise Exception('File not found')
        if ext == '.pdf':
            from pdfminer.high_level import extract_text
            text = extract_text(path)
        elif ext in {'.html', '.htm'}:
            from bs4 import BeautifulSoup
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
                for tag in soup(['script', 'style']): tag.decompose()
                text = soup.get_text(separator='\n')
        elif ext in {'.md', '.txt'}:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        else:
            raise Exception('Unsupported file type')
        text = '\n'.join(line.strip() for line in text.splitlines())
        result['chars'] = len(text)
        result['words'] = len(text.split())
        result['status'] = 'parsed'
        result['ts'] = datetime.utcnow().isoformat()
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        with open(PARSE_LOG, 'a', encoding='utf-8') as logf:
            logf.write(json.dumps({**result, 'action': 'parse'}) + '\n')
    except Exception as e:
        result['error'] = str(e)
    return result

def clean_text_file(parsed_path):
    doc_id = os.path.basename(parsed_path).replace('.txt', '')
    result = {'doc_id': doc_id, 'status': 'error', 'chars': 0, 'words': 0, 'ts': None, 'error': None}
    try:
        if not os.path.exists(parsed_path):
            raise Exception('Parsed file not found')
        with open(parsed_path, 'r', encoding='utf-8') as f:
            text = f.read()
        cleaned = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        cleaned = ' '.join(cleaned.split())
        result['chars'] = len(cleaned)
        result['words'] = len(cleaned.split())
        result['status'] = 'cleaned'
        result['ts'] = datetime.utcnow().isoformat()
        with open(parsed_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        with open(CLEAN_LOG, 'a', encoding='utf-8') as logf:
            logf.write(json.dumps({**result, 'action': 'clean'}) + '\n')
    except Exception as e:
        result['error'] = str(e)
    return result

def update_parsed_stats(doc_id, ext, status, chars, words, last_parsed_iso):
    os.makedirs(os.path.dirname(PARSED_STATS_CSV), exist_ok=True)
    row = [doc_id, ext, status, chars, words, last_parsed_iso]
    with open(PARSED_STATS_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def get_parsed_stats():
    stats = []
    if os.path.exists(PARSED_STATS_CSV):
        with open(PARSED_STATS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 6:
                    stats.append({
                        'doc_id': row[0],
                        'ext': row[1],
                        'status': row[2],
                        'chars': int(row[3]),
                        'words': int(row[4]),
                        'last_parsed_iso': row[5]
                    })
    return stats
