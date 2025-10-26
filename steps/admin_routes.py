import os
import subprocess
from flask import Blueprint, request, jsonify

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

@admin_bp.route('/build-embeddings', methods=['POST'])
def build_embeddings():
    admin_secret = os.environ.get('ADMIN_SECRET', '')
    header_secret = request.headers.get('X-Admin-Secret', '')
    if not admin_secret or header_secret != admin_secret:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
    try:
        subprocess.check_call([
            'python', 'scripts/embed_index.py', '--method', 'headings', '--model', 'minilm'
        ])
        return jsonify({'ok': True, 'message': 'Embeddings built successfully.'})
    except subprocess.CalledProcessError as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
