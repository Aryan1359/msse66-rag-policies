from flask import Blueprint, render_template, request
import os, json
from datetime import datetime, timedelta

step8_bp = Blueprint('step8_bp', __name__, url_prefix='/steps/8')

LOG_SEARCH = "steps/step6/logs/search.jsonl"
LOG_ASK = "steps/step7/logs/ask.jsonl"

# Helpers
def _read_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r') as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows

def _within_window(ts, window):
    if not ts:
        return False
    now = datetime.utcnow().timestamp()
    if window == 'all':
        return True
    elif window == '24h':
        return ts >= now - 86400
    elif window == '7d':
        return ts >= now - 604800
    elif window == '30d':
        return ts >= now - 2592000
    return True

def _median(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    vals.sort()
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    else:
        return (vals[mid-1] + vals[mid]) / 2

def _calc_metrics(ask_rows, search_rows):
    n_questions = sum(1 for r in ask_rows if r.get('status') in {'ok','no_citations'})
    grounded = [r for r in ask_rows if r.get('citations') and len(r['citations']) >= 1]
    grounded_rate = round(100 * len(grounded) / n_questions, 1) if n_questions else 0.0
    # Citation correctness
    correct = 0
    total = 0
    for r in grounded:
        used_ids = set(f"{doc}#{chunk}" for doc,chunk in r.get('used_ids',[]))
        citations = set(r.get('citations',[]))
        if citations and all(c in used_ids for c in citations):
            correct += 1
        total += 1
    citation_correctness = round(100 * correct / total, 1) if total else 0.0
    # Latency
    gen_latencies = [r.get('latency') for r in ask_rows if r.get('latency') is not None]
    median_gen = _median(gen_latencies)
    ret_latencies = [r.get('retrieval_latency') for r in ask_rows if r.get('retrieval_latency') is not None]
    median_ret = _median(ret_latencies)
    end_to_end = median_gen + median_ret if median_gen and median_ret else None
    return {
        'n_questions': n_questions,
        'grounded_rate': grounded_rate,
        'citation_correctness': citation_correctness,
        'median_gen': round(median_gen*1000,1) if median_gen else None,
        'median_ret': round(median_ret*1000,1) if median_ret else None,
        'end_to_end': round(end_to_end*1000,1) if end_to_end else None
    }

@step8_bp.route('', methods=['GET','POST'])
def step8_page():
    window = request.form.get('window','all')
    ask_rows = _read_jsonl(LOG_ASK)
    search_rows = _read_jsonl(LOG_SEARCH)
    # Filter by time window
    ask_rows = [r for r in ask_rows if _within_window(r.get('timestamp'), window)]
    metrics = _calc_metrics(ask_rows, search_rows)
    recent = sorted(ask_rows, key=lambda r: r.get('timestamp',0), reverse=True)[:20]
    for r in recent:
        r['time'] = datetime.fromtimestamp(r.get('timestamp',0)).strftime('%Y-%m-%d %H:%M:%S')
        r['citations_count'] = len(r.get('citations',[])) if r.get('citations') else 0
        r['latency_ms'] = round(r.get('latency',0)*1000,1) if r.get('latency') else None
    no_data = not ask_rows
    return render_template('steps/step_8.html',
        metrics=metrics,
        recent=recent,
        window=window,
        no_data=no_data
    )