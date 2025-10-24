
import os
import json
import numpy as np
import shutil
import hashlib
from datetime import datetime

# Import slugify from Step 4 for consistency
from steps.step4.services_chunk import slugify

def list_chunk_docs(input_dir):
    docs = []
    if not os.path.exists(input_dir):
        return docs
    for fname in sorted(os.listdir(input_dir)):
        if fname.endswith('.jsonl'):
            path = os.path.join(input_dir, fname)
            doc_id = slugify(fname)  # Use consistent slugify
            mtime = os.path.getmtime(path)
            n_chunks = None
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    n_chunks = sum(1 for _ in f)
            except Exception:
                pass
            docs.append({'doc_id': doc_id, 'path': path, 'filename': fname, 'mtime': mtime, 'n_chunks': n_chunks})
    return docs

def load_chunks_for_docs(docs):
    texts = []
    meta_rows = []
    for doc in docs:
        # Compute source_hash for this file
        with open(doc['path'], 'rb') as fbin:
            file_bytes = fbin.read()
            source_hash = hashlib.sha256(file_bytes).hexdigest()
        with open(doc['path'], 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                texts.append(rec['text'])
                meta = {
                    'doc_id': rec.get('doc_id'),
                    'chunk_id': rec.get('chunk_id'),
                    'source_file': doc['filename'],
                    'method': rec.get('method'),
                    'params': rec.get('params'),
                    'source_hash': source_hash,
                    'text': rec.get('text'),
                }
                meta_rows.append(meta)
    return texts, meta_rows

def embed_minilm(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    return np.array(vectors, dtype=np.float32)

def embed_openai(texts):
    import os
    import openai
    import numpy as np
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY not set in environment')
    openai.api_key = api_key
    model = 'text-embedding-3-small'
    vectors = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        resp = openai.Embedding.create(input=batch, model=model)
        for item in resp['data']:
            vectors.append(item['embedding'])
    return np.array(vectors, dtype=np.float32)

def save_artifacts(out_dir, vectors, meta_rows, config_dict, chunk_docs=None):
    os.makedirs(out_dir, exist_ok=True)
    # Ensure float32
    vectors = np.array(vectors, dtype=np.float32)
    # Integrity checks
    n_chunks = len(meta_rows)
    if vectors.shape[0] != n_chunks:
        raise Exception(f"Mismatch: vectors rows ({vectors.shape[0]}) != meta rows ({n_chunks})")
    dim = vectors.shape[1] if n_chunks > 0 else 0
    for i, meta in enumerate(meta_rows):
        meta['vector_index'] = i
        if meta.get('vector_index', i) != i:
            meta['vector_index'] = i
    # Save vectors
    np.save(os.path.join(out_dir, 'vectors.npy'), vectors)
    # Save meta
    with open(os.path.join(out_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta_rows, f, indent=2, ensure_ascii=False)
    # Prepare source_hashes for config
    source_hashes = []
    if chunk_docs:
        for doc in chunk_docs:
            with open(doc['path'], 'rb') as fbin:
                file_bytes = fbin.read()
                source_hash = hashlib.sha256(file_bytes).hexdigest()
            source_hashes.append({
                'doc_id': doc['doc_id'],
                'source_file': doc['filename'],
                'source_hash': source_hash
            })
    # Save config
    config_dict = dict(config_dict)
    config_dict['source_hashes'] = source_hashes
    with open(os.path.join(out_dir, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
    # Save stats
    stats = {'n_chunks': n_chunks, 'dim': dim}
    with open(os.path.join(out_dir, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    # Optional: FAISS
    faiss_status = False
    try:
        import faiss
        # L2-normalize vectors
        if n_chunks > 0 and dim > 0:
            vecs_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
            index = faiss.IndexFlatIP(dim)
            index.add(vecs_norm)
            faiss.write_index(index, os.path.join(out_dir, 'faiss.index'))
            faiss_status = True
    except ImportError:
        faiss_status = False
    # Record faiss status in config
    config_dict['faiss'] = faiss_status
    if faiss_status:
        config_dict['metric'] = 'cosine (IP on L2-normalized vectors)'
    with open(os.path.join(out_dir, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
    return faiss_status

def delete_db_folder(out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
