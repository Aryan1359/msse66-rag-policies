from pathlib import Path
import os, json, numpy as np
import requests

# Portable project root and embeddings dir helpers
def _project_root() -> Path:
    return Path(os.environ.get("PROJECT_ROOT", Path.cwd()))

def _embeddings_dir() -> Path:
    base = os.environ.get("EMBED_DIR")
    return Path(base) if base else _project_root() / "steps" / "step5" / "Embeddings"
def validate_answer(answer: str, citations: list) -> str:
    """Validate the answer and citations. Returns a warning string if validation fails, else empty string."""
    if not answer or not isinstance(answer, str) or not answer.strip():
        return "Answer is empty."
    if not citations:
        return "No citations found in answer."
    return ""
_load_db_logged = False

from .services_rag_exceptions import EmbeddingsMissing

def embeddings_ready(method='headings'):
    folder = _embeddings_dir() / f"{method}__minilm"
    vectors_path = folder / "vectors.npy"
    meta_path = folder / "meta.json"
    return vectors_path.exists() and meta_path.exists()

def load_db(method='headings'):
    """
    Load embeddings and metadata for Step 7 RAG from Step 5 output folders.
    method: 'headings' or 'token'
    """
    global _load_db_logged
    folder = _embeddings_dir() / f"{method}__minilm"
    vectors_path = folder / "vectors.npy"
    meta_path = folder / "meta.json"
    if not _load_db_logged:
        try:
            from flask import current_app
            current_app.logger.info(f"[load_db] Using embeddings folder: {folder.resolve()}")
        except Exception:
            print(f"[load_db] Using embeddings folder: {folder.resolve()}")
        _load_db_logged = True
    if not vectors_path.exists() or not meta_path.exists():
        raise EmbeddingsMissing(method, folder.resolve())
    vectors = np.load(str(vectors_path))
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    return vectors, meta

def embed_query(query, config):
    method = config.get('embed_method', 'minilm')
    if method == 'minilm':
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode([query], convert_to_numpy=True)[0].astype(np.float32)
    raise ValueError('Unknown embedding method')

def retrieve_chunks(q_vec, vectors, meta, topk, min_score=None):
    import time
    t0 = time.time()
    vecs_norm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9)
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-9)
    try:
        import faiss
        index = faiss.IndexFlatIP(vecs_norm.shape[1])
        index.add(vecs_norm)
        D, I = index.search(np.expand_dims(q_norm, axis=0), topk)
        scores = D[0]
        indices = I[0]
    except Exception:
        # fallback: numpy cosine similarity
        scores_raw = np.dot(vecs_norm, q_norm)
        if len(scores_raw) < topk:
            topk = len(scores_raw)
        indices = np.argpartition(scores_raw, -topk)[-topk:]
        indices = indices[np.argsort(scores_raw[indices])[::-1]]
        scores = scores_raw[indices]
    chunks = []
    for rank, (idx, score) in enumerate(zip(indices, scores), 1):
        if min_score is not None and score < min_score:
            continue
        meta_row = meta[idx]
        chunks.append({
            'rank': rank,
            'score': float(score),
            'doc_id': meta_row.get('doc_id'),
            'chunk_id': meta_row.get('chunk_id'),
            'method': meta_row.get('method'),
            'snippet': meta_row.get('text', '')[:200],
            'text': meta_row.get('text', '')
        })
    latency = time.time() - t0
    return chunks, latency

def build_prompt(chunks, question, answer_len):
    context = ''
    for c in chunks:
        context += f"[doc_id: {c['doc_id']} | chunk_id: {c['chunk_id']} | score: {c['score']:.3f}]\n{c['text']}\n\n"
    length_map = {'short': 120, 'med': 250, 'long': 400}
    word_limit = length_map.get(answer_len, 120)
    prompt = f"""
SYSTEM:
You are a strict RAG assistant. You must answer ONLY using the provided CONTEXT below. If the answer is not present in the CONTEXT, reply exactly: 'I can only answer about our policies based on the provided documents.'
Every factual statement MUST be followed by a citation in the format doc_id#chunk_id (e.g., rubric#5). Do NOT use any outside knowledge. Do NOT speculate. Do NOT answer if the information is not present in the CONTEXT.
Limit your answer to {word_limit} words.

CONTEXT:
{context}

USER QUESTION:
{question}
"""
    return prompt

def call_provider(provider: str, prompt: str, answer_len: str) -> dict:
    """
    Call the selected LLM provider and return:
      {"ok": True, "answer": str, "model": str}
    or
      {"ok": False, "error": str}

    Providers:
      - "openrouter_free": uses OPENROUTER_API_KEY
      - "groq": uses GROQ_API_KEY
      - "openai": uses OPENAI_API_KEY
    """
    try:
        # Strict timeouts: connect=5s, read=15s (total=20s)
        timeout = (5, 15)
        max_words = {"short": 120, "medium": 250, "long": 400}.get(answer_len, 120)

        if provider == "openrouter_free":
            api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            if not api_key:
                return {"ok": False, "error": "OpenRouter not configured. Set OPENROUTER_API_KEY."}

            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": "openrouter/auto",
                "messages": [
                    {"role": "system", "content": f"Be concise. Stay within {max_words} words."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
            if resp.status_code != 200:
                return {"ok": False, "error": f"OpenRouter HTTP {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            text = (data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")) or ""
            model = data.get("model", "openrouter/auto")
            return {"ok": True, "answer": text, "model": model}

        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            if not api_key:
                return {"ok": False, "error": "Groq not configured. Set GROQ_API_KEY."}

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": f"Be concise. Stay within {max_words} words."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
            if resp.status_code != 200:
                return {"ok": False, "error": f"Groq HTTP {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            text = (data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")) or ""
            model = data.get("model", "groq/llama3-8b-8192")
            return {"ok": True, "answer": text, "model": model}

        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key:
                return {"ok": False, "error": "OpenAI not configured. Set OPENAI_API_KEY."}

            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": f"Be concise. Stay within {max_words} words."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
            if resp.status_code != 200:
                return {"ok": False, "error": f"OpenAI HTTP {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            text = (data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")) or ""
            model = data.get("model", "gpt-4o-mini")
            return {"ok": True, "answer": text, "model": model}

        else:
            return {"ok": False, "error": f"Unknown provider: {provider}"}

    except requests.Timeout:
        return {"ok": False, "error": f"{provider}: request timed out after 20s"}
    except requests.RequestException as e:
        return {"ok": False, "error": f"{provider}: network error: {str(e)[:200]}"}
    except Exception as e:
        return {"ok": False, "error": f"{provider}: unexpected error: {str(e)[:200]}"}
