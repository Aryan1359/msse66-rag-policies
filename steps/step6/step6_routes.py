import os
import json
import time
import numpy as np
import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, Response
from werkzeug.utils import secure_filename

step6_bp = Blueprint('step6_bp', __name__, url_prefix='/steps/6')


# --- Download CSV route (must be after all other routes) ---
@step6_bp.route('/download_csv', methods=['POST'])
def download_csv():
    dbs = scan_embedding_dbs()
    db_key = request.form.get('db_key')
    topk = int(request.form.get('topk', 5))
    query = request.form.get('query', '').strip()
    selected_db_obj = next((db for db in dbs if db['key'] == db_key), None)
    db_info = selected_db_obj
    if not db_info:
        return Response('Selected embedding DB not found.', status=404)
    vectors_path = os.path.join(db_info['path'], 'vectors.npy')
    meta_path = os.path.join(db_info['path'], 'meta.json')
    config_path = os.path.join(db_info['path'], 'config.json')
    if not (os.path.exists(vectors_path) and os.path.exists(meta_path) and os.path.exists(config_path)):
        return Response('Embedding DB is missing required files.', status=404)
    vectors = np.load(vectors_path).astype(np.float32)
    with open(meta_path, 'r') as f:
        meta_rows = json.load(f)
    with open(config_path, 'r') as f:
        config = json.load(f)
    dim = vectors.shape[1]
    n_chunks = vectors.shape[0]
    if topk > n_chunks:
        topk = n_chunks
    # Embed query
    method = config.get('embed_method', 'minilm')
    if method == 'minilm':
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        q_vec = model.encode([query], convert_to_numpy=True)[0].astype(np.float32)
    else:
        return Response('Unknown embedding method.', status=400)
    vecs_norm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9)
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-9)
    try:
        import faiss
        if db_key not in faiss_indexes:
            index = faiss.IndexFlatIP(dim)
            index.add(vecs_norm)
            faiss_indexes[db_key] = index
        index = faiss_indexes[db_key]
        D, I = index.search(np.expand_dims(q_norm, axis=0), topk)
        scores = D[0]
        indices = I[0]
    except ImportError:
        scores = np.dot(vecs_norm, q_norm)
        indices = np.argpartition(scores, -topk)[-topk:]
        indices = indices[np.argsort(scores[indices])[::-1]]
        scores = scores[indices]
    # Prepare CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Rank', 'Score', 'doc_id', 'chunk_id', 'method', 'source_file', 'Snippet', 'Full Text'])
    for rank, (idx, score) in enumerate(zip(indices, scores), 1):
        meta = meta_rows[idx]
        snippet = meta.get('text', '')[:200] if 'text' in meta else ''
        full_text = meta.get('text', '')
        writer.writerow([
            rank,
            '%.3f' % float(score),
            meta.get('doc_id'),
            meta.get('chunk_id'),
            meta.get('method'),
            meta.get('source_file'),
            snippet,
            full_text
        ])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename=search_results_{db_key}.csv'
    })
import os
import json
import time
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

step6_bp = Blueprint('step6_bp', __name__, url_prefix='/steps/6')

DB_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step5', 'Embeddings')
CACHE_ROOT = os.path.join(os.path.dirname(__file__), 'cache')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'logs', 'search.jsonl')

# Helper to scan available DBs
def scan_embedding_dbs():
    dbs = []
    if not os.path.exists(DB_ROOT):
        return dbs
    for sub in sorted(os.listdir(DB_ROOT)):
        subdir = os.path.join(DB_ROOT, sub)
        if os.path.isdir(subdir):
            stats_path = os.path.join(subdir, 'stats.json')
            config_path = os.path.join(subdir, 'config.json')
            if os.path.exists(stats_path) and os.path.exists(config_path):
                with open(stats_path, 'r') as f:
                    stats = json.load(f)
                with open(config_path, 'r') as f:
                    config = json.load(f)
                dbs.append({
                    'key': sub,
                    'path': subdir,
                    'stats': stats,
                    'config': config
                })
    return dbs

# Global FAISS cache
faiss_indexes = {}

@step6_bp.route('', methods=['GET'])
def step6_page():
    dbs = scan_embedding_dbs()
    selected_db = dbs[0]['key'] if dbs else None
    selected_db_obj = dbs[0] if dbs else None
    topk = 5
    query = ''
    results = None
    latency_ms = None
    embed_history = []
    # Optionally read Step 5 embed log
    embed_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step5', 'logs', 'embed.jsonl')
    if os.path.exists(embed_log_path):
        with open(embed_log_path, 'r') as f:
            for line in f:
                try:
                    embed_history.append(json.loads(line))
                except Exception:
                    continue
    return render_template('steps/step_6.html',
        dbs=dbs,
        selected_db=selected_db,
        selected_db_obj=selected_db_obj,
        topk=topk,
        query=query,
        results=results,
        latency_ms=latency_ms,
        embed_history=embed_history
    )

@step6_bp.route('/search', methods=['POST'])
def search_route():
    dbs = scan_embedding_dbs()
    db_key = request.form.get('db_key')
    topk = int(request.form.get('topk', 5))
    query = request.form.get('query', '').strip()
    results = []
    latency_ms = None
    selected_db = db_key
    selected_db_obj = next((db for db in dbs if db['key'] == db_key), None)
    db_info = selected_db_obj
    if not db_info:
        flash('Selected embedding DB not found. Please choose another.', 'danger')
        return redirect(url_for('step6_bp.step6_page'))
    # Check required files
    vectors_path = os.path.join(db_info['path'], 'vectors.npy')
    meta_path = os.path.join(db_info['path'], 'meta.json')
    config_path = os.path.join(db_info['path'], 'config.json')
    if not (os.path.exists(vectors_path) and os.path.exists(meta_path) and os.path.exists(config_path)):
        flash('Embedding DB is missing required files. Please return to Step 5 and run Embed.', 'danger')
        return redirect(url_for('step6_bp.step6_page'))
    if not query:
        flash('Please enter a query to search.', 'warning')
        return redirect(url_for('step6_bp.step6_page'))
    # Load vectors and meta
    t0 = time.time()
    vectors = np.load(vectors_path).astype(np.float32)
    with open(meta_path, 'r') as f:
        meta_rows = json.load(f)
    with open(config_path, 'r') as f:
        config = json.load(f)
    dim = vectors.shape[1]
    # Clamp topk to available chunks
    n_chunks = vectors.shape[0]
    if topk > n_chunks:
        topk = n_chunks
    # Embed query
    method = config.get('embed_method', 'minilm')
    if method == 'minilm':
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            flash('MiniLM embedding requires sentence-transformers. Please install: pip install sentence-transformers', 'danger')
            return redirect(url_for('step6_bp.step6_page'))
        model = SentenceTransformer('all-MiniLM-L6-v2')
        q_vec = model.encode([query], convert_to_numpy=True)[0].astype(np.float32)
    else:
        flash(f'Unknown embedding method: {method}', 'danger')
        return redirect(url_for('step6_bp.step6_page'))
    # Normalize vectors
    vecs_norm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9)
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-9)
    # Try FAISS
    faiss_used = False
    try:
        import faiss
        if db_key not in faiss_indexes:
            index = faiss.IndexFlatIP(dim)
            index.add(vecs_norm)
            faiss_indexes[db_key] = index
        index = faiss_indexes[db_key]
        D, I = index.search(np.expand_dims(q_norm, axis=0), topk)
        scores = D[0]
        indices = I[0]
        faiss_used = True
    except ImportError:
        # NumPy fallback
        scores = np.dot(vecs_norm, q_norm)
        indices = np.argpartition(scores, -topk)[-topk:]
        indices = indices[np.argsort(scores[indices])[::-1]]
        scores = scores[indices]
    # Gather results
    for rank, (idx, score) in enumerate(zip(indices, scores), 1):
        meta = meta_rows[idx]
        snippet = meta.get('text', '')[:200] if 'text' in meta else ''
        results.append({
            'rank': rank,
            'score': float(score),
            'doc_id': meta.get('doc_id'),
            'chunk_id': meta.get('chunk_id'),
            'method': meta.get('method'),
            'source_file': meta.get('source_file'),
            'snippet': snippet,
            'full_text': meta.get('text', '')
        })
    latency_ms = int((time.time() - t0) * 1000)
    # Log search
    log_entry = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'db': db_key,
        'topk': topk,
        'latency_ms': latency_ms,
        'query': query[:80],
        'result_ids': [[r['doc_id'], r['chunk_id']] for r in results]
    }
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    # Optionally read Step 5 embed log
    embed_history = []
    embed_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step5', 'logs', 'embed.jsonl')
    if os.path.exists(embed_log_path):
        with open(embed_log_path, 'r') as f:
            for line in f:
                try:
                    embed_history.append(json.loads(line))
                except Exception:
                    continue
    return render_template('steps/step_6.html',
        dbs=dbs,
        selected_db=db_key,
        selected_db_obj=selected_db_obj,
        topk=topk,
        query=query,
        results=results,
        latency_ms=latency_ms,
        faiss_used=faiss_used,
        embed_history=embed_history
    )

@step6_bp.route('/clear', methods=['POST'])
def clear_route():
    dbs = scan_embedding_dbs()
    selected_db = dbs[0]['key'] if dbs else None
    topk = 5
    query = ''
    results = None
    latency_ms = None
    embed_history = []
    embed_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step5', 'logs', 'embed.jsonl')
    if os.path.exists(embed_log_path):
        with open(embed_log_path, 'r') as f:
            for line in f:
                try:
                    embed_history.append(json.loads(line))
                except Exception:
                    continue
    return render_template('steps/step_6.html',
        dbs=dbs,
        selected_db=selected_db,
        topk=topk,
        query=query,
        results=results,
        latency_ms=latency_ms,
        embed_history=embed_history
    )
