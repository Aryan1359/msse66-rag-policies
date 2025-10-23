import os
import json
import shutil
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .services_embed import (
    list_chunk_docs, load_chunks_for_docs, embed_minilm, embed_openai,
    save_artifacts, delete_db_folder
)

step5_bp = Blueprint('step5_bp', __name__, url_prefix='/steps/5')

CHUNK_DIRS = {
    'headings': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step4', 'Chunked-by-Heading'),
    'token': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step4', 'Chunked-by-Token'),
}
EMBED_ROOT = os.path.join(os.path.dirname(__file__), 'Embeddings')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'logs', 'embed.jsonl')

EMBED_METHODS = {
    'minilm': {
        'name': 'MiniLM (local)',
        'model': 'all-MiniLM-L6-v2',
        'enabled': True
    },
    'openai': {
        'name': 'OpenAI',
        'model': 'text-embedding-3-small',
        'enabled': False
    }
}
try:
    import dotenv
    from dotenv import load_dotenv
    load_dotenv()
    if os.getenv('OPENAI_API_KEY'):
        EMBED_METHODS['openai']['enabled'] = True
except Exception:
    pass

def get_embed_subdir(chunk_source, embed_method):
    return os.path.join(EMBED_ROOT, f'{chunk_source}__{embed_method}')

@step5_bp.route('', methods=['GET'])
def step5_page():
    chunk_source = request.args.get('chunk_source', 'headings')
    embed_method = request.args.get('embed_method', 'minilm')
    chunk_dir = CHUNK_DIRS.get(chunk_source, CHUNK_DIRS['headings'])
    docs = list_chunk_docs(chunk_dir)
    preview = None
    summary = None
    meta_rows = []
    config = None
    stats = None
    embed_subdir = get_embed_subdir(chunk_source, embed_method)
    meta_path = os.path.join(embed_subdir, 'meta.json')
    config_path = os.path.join(embed_subdir, 'config.json')
    stats_path = os.path.join(embed_subdir, 'stats.json')
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_rows = json.load(f)
            preview = meta_rows[:3]
        except Exception:
            preview = None
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    if os.path.exists(stats_path):
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    return render_template('steps/step_5.html',
        chunk_source=chunk_source,
        embed_method=embed_method,
        docs=docs,
        preview=preview,
        config=config,
        stats=stats,
        embed_methods=EMBED_METHODS,
        embed_subdir=embed_subdir
    )

@step5_bp.route('/embed', methods=['POST'])
def embed_route():
    chunk_source = request.form.get('chunk_source', 'headings')
    embed_method = request.form.get('embed_method', 'minilm')
    selected_doc_ids = request.form.get('selected_doc_ids', '')
    chunk_dir = CHUNK_DIRS.get(chunk_source, CHUNK_DIRS['headings'])
    docs = list_chunk_docs(chunk_dir)
    if request.form.get('submit') == 'all':
        doc_ids = [d['doc_id'] for d in docs]
    else:
        doc_ids = [d for d in selected_doc_ids.split(',') if d]
        if not doc_ids:
            flash('No documents selected for embedding.', 'warning')
            return redirect(url_for('step5_bp.step5_page', chunk_source=chunk_source, embed_method=embed_method))
    selected_docs = [d for d in docs if d['doc_id'] in doc_ids]
    texts, meta_rows = load_chunks_for_docs(selected_docs)
    t0 = time.time()
    try:
        if embed_method == 'minilm':
            vectors = embed_minilm(texts)
            model_name = EMBED_METHODS['minilm']['model']
        elif embed_method == 'openai':
            if not EMBED_METHODS['openai']['enabled']:
                raise RuntimeError('OpenAI embedding is not enabled (missing API key).')
            vectors = embed_openai(texts)
            model_name = EMBED_METHODS['openai']['model']
        else:
            raise RuntimeError(f'Unknown embedding method: {embed_method}')
        out_dir = get_embed_subdir(chunk_source, embed_method)
        config_dict = {
            'chunk_source': chunk_source,
            'embed_method': embed_method,
            'model': model_name,
            'created_iso': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        save_artifacts(out_dir, vectors, meta_rows, config_dict)
        ms_elapsed = int((time.time() - t0) * 1000)
        stats = {'n_chunks': len(texts), 'dim': vectors.shape[1], 'build_ms': ms_elapsed}
        with open(os.path.join(out_dir, 'stats.json'), 'w', encoding='utf-8') as f:
            json.dump(stats, f)
        log_entry = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'chunk_source': chunk_source,
            'embed_method': embed_method,
            'n_chunks': len(texts),
            'dim': vectors.shape[1],
            'ms_elapsed': ms_elapsed,
            'status': 'ok'
        }
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        flash(f'Embedded {len(texts)} chunks with {embed_method}.', 'success')
    except Exception as e:
        log_entry = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'chunk_source': chunk_source,
            'embed_method': embed_method,
            'n_chunks': len(texts),
            'dim': None,
            'ms_elapsed': int((time.time() - t0) * 1000),
            'status': 'error',
            'error': str(e)
        }
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        flash(f'Error embedding: {e}', 'danger')
    return redirect(url_for('step5_bp.step5_page', chunk_source=chunk_source, embed_method=embed_method))

@step5_bp.route('/delete_db', methods=['POST'])
def delete_db_route():
    chunk_source = request.form.get('chunk_source', 'headings')
    embed_method = request.form.get('embed_method', 'minilm')
    out_dir = get_embed_subdir(chunk_source, embed_method)
    try:
        delete_db_folder(out_dir)
        flash(f'Database for {chunk_source}__{embed_method} deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting DB: {e}', 'danger')
    return redirect(url_for('step5_bp.step5_page', chunk_source=chunk_source, embed_method=embed_method))
