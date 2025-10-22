
"""
Step 3 API: List files from parsed_raw, clean all, save results in data/parsed, update stats/logs.
"""
import os
import json
from flask import Blueprint, request, jsonify
from services.ingest_utils import slugify, clean_text, get_parsed_stats

PARSED_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step2', 'Parse-Results')

step3_bp = Blueprint('step3_bp', __name__, url_prefix='/api/step3')

def list_parsed_raw_files():
    files = []
    for fname in os.listdir(PARSED_RAW_DIR):
        fpath = os.path.join(PARSED_RAW_DIR, fname)
        if os.path.isfile(fpath):
            files.append({
                'name': fname,
                'size': os.path.getsize(fpath),
                'mtime': os.path.getmtime(fpath)
            })
    return files

@step3_bp.route('/files', methods=['GET'])
def api_list_files():
    return jsonify({'files': list_parsed_raw_files()})

@step3_bp.route('/clean', methods=['POST'])
def api_clean():
    results = []
    for fname in os.listdir(PARSED_RAW_DIR):
        fpath = os.path.join(PARSED_RAW_DIR, fname)
        if os.path.isfile(fpath):
            res = clean_text(fpath)
            results.append(res)
    return jsonify({'results': results, 'stats': get_parsed_stats()})
