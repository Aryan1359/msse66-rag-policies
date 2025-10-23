import os
import re
import json
from datetime import datetime

STEP3_CLEAN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step3', 'Clean-Results')
CHUNKED_HEADING_DIR = os.path.join(os.path.dirname(__file__), 'Chunked-by-Heading')
CHUNKED_TOKEN_DIR = os.path.join(os.path.dirname(__file__), 'Chunked-by-Token')
CHUNK_LOG = os.path.join(os.path.dirname(__file__), 'logs', 'chunk.jsonl')

def slugify(filename: str) -> str:
	base = os.path.splitext(os.path.basename(filename))[0]
	slug = re.sub(r"[^a-zA-Z0-9]+", "_", base.lower()).strip("_")
	return slug

def list_clean_files():
	files = []
	for fname in os.listdir(STEP3_CLEAN_DIR):
		fpath = os.path.join(STEP3_CLEAN_DIR, fname)
		if os.path.isfile(fpath):
			files.append({
				'doc_id': slugify(fname),
				'filename': fname,
				'size': os.path.getsize(fpath),
				'mtime': os.path.getmtime(fpath)
			})
	return files


def headings_chunk(doc_path, mode, min_heading_gap=1, max_chunk_len=None):
	"""
	Chunk text by headings. Returns list of chunk dicts.
	"""
	with open(doc_path, 'r', encoding='utf-8') as f:
		text = f.read()
	lines = text.splitlines()
	chunks = []
	chunk_lines = []
	chunk_starts = []
	# Identify headings
	for i, line in enumerate(lines):
		is_heading = False
		if mode == 'markdown_atx' and re.match(r'^#{1,6}\s+.+', line):
			is_heading = True
		elif mode == 'setext' and i+1 < len(lines) and re.match(r'^(=+|-+)$', lines[i+1]):
			is_heading = True
		elif mode == 'heuristic':
			if re.match(r'^#{1,6}\s+.+', line):
				is_heading = True
			elif i+1 < len(lines) and re.match(r'^(=+|-+)$', lines[i+1]):
				is_heading = True
			elif len(line) <= 80 and line.endswith(':'):
				is_heading = True
			elif len(line) <= 60 and line.isupper() and (i+1 == len(lines) or lines[i+1].strip() == ''):
				is_heading = True
			elif re.match(r'^(Section|Policy|Purpose|Scope)', line) and (i+1 == len(lines) or lines[i+1].strip() == ''):
				is_heading = True
		if is_heading:
			chunk_starts.append(i)
	# Add start and end
	if chunk_starts and chunk_starts[0] != 0:
		chunk_starts = [0] + chunk_starts
	chunk_starts.append(len(lines))
	# Build chunks
	for idx in range(len(chunk_starts)-1):
		start, end = chunk_starts[idx], chunk_starts[idx+1]
		chunk = '\n'.join(lines[start:end]).strip()
		if chunk:
			chunks.append(chunk)
	# Merge tiny chunks if min_heading_gap > 1
	if min_heading_gap > 1 and len(chunks) > 1:
		merged = []
		buf = chunks[0]
		for c in chunks[1:]:
			if len(buf.split()) < min_heading_gap:
				buf += '\n' + c
			else:
				merged.append(buf)
				buf = c
		merged.append(buf)
		chunks = merged
	# Soft-wrap oversized chunks
	if max_chunk_len:
		wrapped = []
		for chunk in chunks:
			words = chunk.split()
			while len(words) > max_chunk_len:
				wrapped.append(' '.join(words[:max_chunk_len]))
				words = words[max_chunk_len:]
			wrapped.append(' '.join(words))
		chunks = wrapped
	return chunks

def token_chunk(doc_path, window_size=700, overlap=150, tokenization='whitespace_approx'):
	"""
	Chunk text by token windows. Returns list of chunk dicts.
	"""
	with open(doc_path, 'r', encoding='utf-8') as f:
		text = f.read()
	tokens = text.split() if tokenization == 'whitespace_approx' else list(text)
	chunks = []
	i = 0
	while i < len(tokens):
		chunk = ' '.join(tokens[i:i+window_size])
		if chunk:
			chunks.append(chunk)
		i += window_size - overlap
	return chunks

def write_jsonl(chunks, out_path, doc_id, method, params):
	with open(out_path, 'w', encoding='utf-8') as f:
		for idx, chunk in enumerate(chunks):
			rec = {
				'doc_id': doc_id,
				'chunk_id': idx,
				'method': method,
				'params': params,
				'text': chunk
			}
			f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def read_first_chunks(jsonl_path, n=3):
	chunks = []
	if os.path.exists(jsonl_path):
		with open(jsonl_path, 'r', encoding='utf-8') as f:
			for i, line in enumerate(f):
				if i >= n:
					break
				try:
					chunks.append(json.loads(line))
				except Exception:
					continue
	return chunks

def write_log(doc_id, method, n_chunks, ms_elapsed, params, status='ok', error=None):
	log_entry = {
		'ts': datetime.utcnow().isoformat(),
		'doc_id': doc_id,
		'method': method,
		'n_chunks': n_chunks,
		'ms_elapsed': ms_elapsed,
		'params': params,
		'status': status,
		'error': error
	}
	with open(CHUNK_LOG, 'a', encoding='utf-8') as f:
		f.write(json.dumps(log_entry) + '\n')