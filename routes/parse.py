from flask import Blueprint, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
from services.ingest_utils import (
    list_uploaded_files, parse_file, clean_text_file,
    update_parsed_stats, get_parsed_stats, POLICIES_DIR, PARSED_DIR
)

parse_bp = Blueprint('parse_bp', __name__, url_prefix='/api')

@parse_bp.route('/parse', methods=['POST'])
def api_parse():
    data = request.get_json(silent=True) or {}
    doc_ids = data.get('doc_ids')
    files = list_uploaded_files()
    if not doc_ids:
        doc_ids = [f['doc_id'] for f in files]
    parsed, errors = [], []
    for doc_id in doc_ids:
        f = next((x for x in files if x['doc_id'] == doc_id), None)
        if not f:
            errors.append({'doc_id': doc_id, 'error': 'File not found'})
            continue
        res = parse_file(f['path'])
        update_parsed_stats(doc_id, f['ext'], res['status'], res['chars'], res['words'], res['ts'])
        if res['status'] == 'parsed':
            parsed.append(doc_id)
        else:
            errors.append({'doc_id': doc_id, 'error': res['error']})
    return jsonify({'parsed': parsed, 'errors': errors}), 200

@parse_bp.route('/clean', methods=['POST'])
def api_clean():
    data = request.get_json(silent=True) or {}
    doc_ids = data.get('doc_ids')
    files = list_uploaded_files()
    if not doc_ids:
        doc_ids = [f['doc_id'] for f in files]
    cleaned, errors = [], []
    for doc_id in doc_ids:
        parsed_path = os.path.join(PARSED_DIR, doc_id + '.txt')
        if not os.path.exists(parsed_path):
            errors.append({'doc_id': doc_id, 'error': 'Parsed file not found'})
            continue
        res = clean_text_file(parsed_path)
        update_parsed_stats(doc_id, os.path.splitext(doc_id)[1].lower(), res['status'], res['chars'], res['words'], res['ts'])
        if res['status'] == 'cleaned':
            cleaned.append(doc_id)
        else:
            errors.append({'doc_id': doc_id, 'error': res['error']})
    return jsonify({'cleaned': cleaned, 'errors': errors}), 200

@parse_bp.route('/parse_clean', methods=['POST'])
def api_parse_clean():
    data = request.get_json(silent=True) or {}
    doc_ids = data.get('doc_ids')
    files = list_uploaded_files()
    if not doc_ids:
        doc_ids = [f['doc_id'] for f in files]
    results = []
    for doc_id in doc_ids:
        f = next((x for x in files if x['doc_id'] == doc_id), None)
        if not f:
            results.append({'doc_id': doc_id, 'error': 'File not found'})
            continue
        res_parse = parse_file(f['path'])
        update_parsed_stats(doc_id, f['ext'], res_parse['status'], res_parse['chars'], res_parse['words'], res_parse['ts'])
        if res_parse['status'] == 'parsed':
            res_clean = clean_text_file(os.path.join(PARSED_DIR, doc_id + '.txt'))
            update_parsed_stats(doc_id, f['ext'], res_clean['status'], res_clean['chars'], res_clean['words'], res_clean['ts'])
            results.append({'doc_id': doc_id, 'parse': res_parse, 'clean': res_clean})
        else:
            results.append({'doc_id': doc_id, 'parse': res_parse, 'error': res_parse['error']})
    return jsonify(results), 200

@parse_bp.route('/parsed/<doc_id>', methods=['GET'])
def api_parsed(doc_id):
    safe_id = secure_filename(doc_id)
    parsed_path = os.path.join(PARSED_DIR, safe_id + '.txt')
    if not os.path.exists(parsed_path):
        return 'Not parsed yet.', 404
    with open(parsed_path, 'r', encoding='utf-8') as f:
        txt = f.read()
    return txt[:2000], 200, {'Content-Type': 'text/plain; charset=utf-8'}

@parse_bp.route('/parse/stats', methods=['GET'])
def api_parse_stats():
    stats = get_parsed_stats()
    return jsonify(stats), 200

# Step 2 page route
@parse_bp.route('/steps/2', methods=['GET'])
def step_2_page():
    files = []
    for fname in os.listdir(POLICIES_DIR):
        ext = os.path.splitext(fname)[1].lower()
        if ext in {'.md', '.txt', '.pdf', '.html', '.htm'}:
            files.append({
                'doc_id': fname,
                'ext': ext,
                'size': os.path.getsize(os.path.join(POLICIES_DIR, fname)),
            })
    return render_template('steps/step_2.html', files=files)
