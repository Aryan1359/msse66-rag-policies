import os
import json
import time
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from .services_rag import load_db, embed_query, retrieve_chunks, build_prompt, call_provider, validate_answer

step7_bp = Blueprint('step7_bp', __name__, url_prefix='/steps/7')


def load_api_keys():
    key_path = os.path.join(os.path.dirname(__file__), 'api_keys.json')
    if not os.path.exists(key_path):
        return {"OPENROUTER_API_KEY": "", "GROQ_API_KEY": "", "OPENAI_API_KEY": "", "USE_ENV_OPENROUTER": False}
    with open(key_path, 'r') as f:
        keys = json.load(f)
        # Add flag if missing
        if "USE_ENV_OPENROUTER" not in keys:
            keys["USE_ENV_OPENROUTER"] = False
        return keys

def save_api_keys(keys):
    key_path = os.path.join(os.path.dirname(__file__), 'api_keys.json')
    # Don't store env key value
    if keys.get("USE_ENV_OPENROUTER"):
        keys["OPENROUTER_API_KEY"] = ""
    with open(key_path, 'w') as f:
        json.dump(keys, f, indent=2)

@step7_bp.route('/api_keys', methods=['POST'])
def api_keys():
    # Handle add/edit/delete API keys
    if 'delete' in request.form:
        keys = {"OPENROUTER_API_KEY": "", "GROQ_API_KEY": "", "OPENAI_API_KEY": "", "USE_ENV_OPENROUTER": False}
        save_api_keys(keys)
        flash('All API keys deleted.', 'success')
    elif 'use_env_openrouter' in request.form:
        keys = load_api_keys()
        keys["USE_ENV_OPENROUTER"] = True
        save_api_keys(keys)
        flash('OpenRouter API key will be loaded from repo secret.', 'success')
    elif 'openrouter_key' in request.form and request.form.get('openrouter_key', '').strip():
        # Store key in session, not disk
        session['OPENROUTER_API_KEY'] = request.form.get('openrouter_key', '').strip()
        flash('OpenRouter API key set for this session only.', 'success')
    else:
        keys = load_api_keys()
        keys["GROQ_API_KEY"] = request.form.get('groq_key', '').strip()
        keys["OPENAI_API_KEY"] = request.form.get('openai_key', '').strip()
        keys["USE_ENV_OPENROUTER"] = False
        save_api_keys(keys)
        flash('API keys saved.', 'success')
    return redirect(url_for('step7_bp.step7_page'))

@step7_bp.route('', methods=['GET'])
def step7_page():
    # Allow user to select chunking method (headings or token)
    method = request.args.get('method', 'headings')
    try:
        vectors, meta = load_db(method)
        error = None
    except Exception as e:
        vectors, meta = None, None
        error = str(e)
    providers = ['openrouter_free', 'groq', 'openai']
    api_keys = load_api_keys()
    available_providers = [p for p in providers if (
        (p == 'openrouter_free' and (session.get('OPENROUTER_API_KEY') or api_keys.get('OPENROUTER_API_KEY') or api_keys.get('USE_ENV_OPENROUTER')))
        or (p != 'openrouter_free' and api_keys.get(f'{p.upper().replace("_FREE", "")}_API_KEY'))
    )]
    return render_template('steps/step_7.html',
        vectors=vectors,
        meta=meta,
        method=method,
        providers=providers,
        available_providers=available_providers,
        api_keys=api_keys,
        topk=5,
        min_score='',
        answer_len='short',
        question='',
        answer=None,
        context_chunks=None,
        citations=None,
        provenance=None,
        error=error
    )

@step7_bp.route('/ask', methods=['POST'])
def ask_route():
    method = request.form.get('method', 'headings')
    try:
        vectors, meta = load_db(method)
    except FileNotFoundError:
        from .lazy_build import ensure_embeddings
        ensure_embeddings(method=method, model="minilm")
        vectors, meta = load_db(method)
    topk = int(request.form.get('topk', 5))
    min_score = request.form.get('min_score')
    if min_score == 'None' or min_score is None:
        min_score = None
    else:
        try:
            min_score = float(min_score)
        except Exception:
            min_score = None
    answer_len = request.form.get('answer_len', 'short')
    provider = request.form.get('provider')
    question = request.form.get('question', '').strip()
    # Input validation
    api_keys = load_api_keys()
    providers = ['openrouter_free', 'groq', 'openai']
    available_providers = [p for p in providers if (
        (p == 'openrouter_free' and (session.get('OPENROUTER_API_KEY') or api_keys.get('OPENROUTER_API_KEY') or api_keys.get('USE_ENV_OPENROUTER')))
        or (p != 'openrouter_free' and api_keys.get(f'{p.upper().replace("_FREE", "")}_API_KEY'))
    )]
    if not question:
        flash('Please enter a question.', 'warning')
        return render_template('steps/step_7.html', vectors=vectors, meta=meta, method=method, providers=providers, available_providers=available_providers, api_keys=api_keys, topk=topk, min_score=min_score, answer_len=answer_len, question=question, answer=None, context_chunks=None, citations=None, provenance=None, error=None)
    if min_score:
        try:
            min_score = float(min_score)
            if min_score < -1 or min_score > 1:
                flash('Min Score must be between -1 and 1.', 'warning')
                min_score = None
        except Exception:
            flash('Min Score must be a number.', 'warning')
            min_score = None
    # Retrieve chunks
    # For embedding, use a default config (or extend meta to include config if needed)
    config = {}
    q_vec = embed_query(question, config)
    context_chunks, _ = retrieve_chunks(q_vec, vectors, meta, topk, min_score)
    if not context_chunks:
        error = 'No evidence found with the current threshold; lower it and try again.'
        return render_template('steps/step_7.html', vectors=vectors, meta=meta, method=method, providers=providers, available_providers=available_providers, api_keys=api_keys, topk=topk, min_score=min_score, answer_len=answer_len, question=question, answer=None, context_chunks=None, citations=None, provenance=None, error=error)
    # Build prompt
    prompt = build_prompt(context_chunks, question, answer_len)
    import re
    import time as _time
    try:
        # Set provider API key as env var for call_provider
        key_map = {
            'openrouter_free': 'OPENROUTER_API_KEY',
            'groq': 'GROQ_API_KEY',
            'openai': 'OPENAI_API_KEY'
        }
        if provider == 'openrouter_free':
            if session.get('OPENROUTER_API_KEY'):
                os.environ['OPENROUTER_API_KEY'] = session.get('OPENROUTER_API_KEY')
            elif api_keys.get('USE_ENV_OPENROUTER'):
                os.environ['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', '')
            else:
                os.environ['OPENROUTER_API_KEY'] = api_keys.get('OPENROUTER_API_KEY', '')
        elif provider in key_map:
            os.environ[key_map[provider]] = api_keys.get(key_map[provider], '')
        t0 = _time.time()
        result = call_provider(provider, prompt, answer_len)
        latency = _time.time() - t0
        answer = result.get('answer') if result.get('ok') else None
        # Extract citations in format doc_id#chunk_id (e.g., rubric#5)
        if answer:
            citations = re.findall(r'([\w\-]+#[0-9]+)', answer)
        else:
            citations = []
        error = result.get('error') if not result.get('ok') else None
    except Exception as e:
        error = f"Provider error: {str(e)}"
        answer = None
        citations = None
        latency = None
    # Validate answer
    val_msg = validate_answer(answer, citations)
    if val_msg:
        flash(val_msg, 'warning')
    # Log
    used_ids = [[c['doc_id'], c['chunk_id']] for c in context_chunks]
    log_entry = {
        'timestamp': time.time(),
        'question': question,
        'provider': provider,
        'method': method,
        'topk': topk,
        'min_score': min_score,
        'answer_len': answer_len,
        'latency': latency,
        'citations': citations,
        'used_ids': used_ids,
        'status': 'ok' if not val_msg else 'no_citations',
        'error': error
    }
    log_path = os.path.join(os.path.dirname(__file__), 'logs', 'ask.jsonl')
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    return render_template(
        'steps/step_7.html',
        vectors=vectors,
        meta=meta,
        method=method,
        providers=providers,
        available_providers=available_providers,
        api_keys=api_keys,
        topk=topk,
        min_score=min_score,
        answer_len=answer_len,
        question=question,
        answer=answer,
        context_chunks=context_chunks,
        citations=citations,
        provenance=None,
        error=error
    )
