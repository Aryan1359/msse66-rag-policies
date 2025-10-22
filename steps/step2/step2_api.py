
"""
Step 2 API: List files from step 1, parse all, save results in data/parsed_raw, update stats/logs.
"""
import os
import json
from flask import Blueprint, request, jsonify
from services.ingest_utils import slugify, parse_file, get_parsed_stats

STEP1_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step1', 'data-Policies')

step2_bp = Blueprint('step2_bp', __name__, url_prefix='/api/step2')

def list_step1_files():
    files = []
    for fname in os.listdir(STEP1_DATA):
        fpath = os.path.join(STEP1_DATA, fname)
        if os.path.isfile(fpath):
            files.append({
                'name': fname,
                'size': os.path.getsize(fpath),
                'mtime': os.path.getmtime(fpath)
            })
    return files

@step2_bp.route('/files', methods=['GET'])
def api_list_files():
    return jsonify({'files': list_step1_files()})

@step2_bp.route('/parse', methods=['POST'])
def api_parse():
    results = []
    for fname in os.listdir(STEP1_DATA):
        fpath = os.path.join(STEP1_DATA, fname)
        if os.path.isfile(fpath):
            res = parse_file(fpath)
            results.append(res)
    return jsonify({'results': results, 'stats': get_parsed_stats()})
