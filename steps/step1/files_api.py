import os
import json
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

POLICIES_DIR = os.path.join(os.path.dirname(__file__), 'data-Policies')
INDEX_JSONL = os.path.join(os.path.dirname(__file__), 'data-Policies', 'index.jsonl')
ALLOWED_EXTS = {'.md', '.txt', '.pdf', '.html', '.htm'}

def _infer_name(rec):
	for k in ('source', 'path', 'file'):
		v = rec.get(k)
		if isinstance(v, str) and v.strip():
			return os.path.basename(v)
	meta = rec.get('meta') or {}
	for k in ('source', 'path', 'file'):
		v = meta.get(k)
		if isinstance(v, str) and v.strip():
			return os.path.basename(v)
	v = rec.get('doc_id') or meta.get('doc_id')
	if isinstance(v, str) and v.strip():
		return v
	return 'unknown'

def _list_files_payload():
	files = []
	for fname in os.listdir(POLICIES_DIR):
		fpath = os.path.join(POLICIES_DIR, fname)
		if os.path.isfile(fpath):
			files.append({
				'name': fname,
				'size': os.path.getsize(fpath),
				'mtime': os.path.getmtime(fpath),
				'chunk_count': 1
			})
	return {'files': sorted(files, key=lambda x: x['name'].lower()), 'count': len(files)}

def _allowed(filename: str) -> bool:
	return os.path.splitext(filename)[1].lower() in ALLOWED_EXTS

def api_files():
	if request.method == 'POST':
		if 'file' not in request.files:
			return jsonify({'ok': False, 'error': 'missing file'}), 400
		f = request.files['file']
		if not f or not f.filename:
			return jsonify({'ok': False, 'error': 'empty filename'}), 400
		name = secure_filename(f.filename)
		if not _allowed(name):
			return jsonify({'ok': False, 'error': 'unsupported extension'}), 400
		os.makedirs(POLICIES_DIR, exist_ok=True)
		dst = os.path.join(POLICIES_DIR, name)
		f.save(dst)
		import subprocess
		subprocess.run(['python', 'scripts/index_jsonl.py', '--dir', POLICIES_DIR], check=True)
		payload = _list_files_payload()
		return jsonify(payload), 201
	payload = _list_files_payload()
	return jsonify(payload), 200

def api_files_delete(fname):
	name = secure_filename(os.path.basename(fname))
	if not name:
		return jsonify({'ok': False, 'error': 'invalid name'}), 400
	p = os.path.join(POLICIES_DIR, name)
	if not os.path.exists(p):
		return jsonify({'ok': False, 'error': 'not found'}), 404
	try:
		os.remove(p)
	except Exception as e:
		return jsonify({'ok': False, 'error': f'delete failed: {e}'}), 500
	import subprocess
	subprocess.run(['python', 'scripts/index_jsonl.py', '--dir', POLICIES_DIR], check=True)
	return jsonify(_list_files_payload()), 200

def api_files_raw(fname):
	name = secure_filename(os.path.basename(fname))
	p = os.path.join(POLICIES_DIR, name)
	if not os.path.exists(p):
		return jsonify({'ok': False, 'error': 'not found'}), 404
	return send_from_directory(POLICIES_DIR, name)