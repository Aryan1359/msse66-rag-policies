from flask import Blueprint
from steps.step1.files_api import api_files, api_files_delete, api_files_raw

files_bp = Blueprint('files_bp', __name__, url_prefix='/api')

files_bp.route('/files', methods=['GET', 'POST'])(api_files)
files_bp.route('/files/<path:fname>', methods=['DELETE'])(api_files_delete)
files_bp.route('/files/raw/<path:fname>', methods=['GET'])(api_files_raw)
