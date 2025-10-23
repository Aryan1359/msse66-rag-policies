import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .services_chunk import list_clean_files, slugify, headings_chunk, token_chunk, write_jsonl, read_first_chunks, write_log

step4_bp = Blueprint('step4_bp', __name__, url_prefix='/steps/4')

@step4_bp.route('', methods=['GET'])
def step4_page():
	files = list_clean_files()
	return render_template('steps/step_4.html', files=files, preview_headings_chunks=None, preview_token_chunks=None)

@step4_bp.route('/chunk_headings', methods=['POST'])
def chunk_headings():
	import time
	files = list_clean_files()
	mode = request.form.get('mode', 'markdown_atx')
	min_heading_gap = int(request.form.get('min_heading_gap', 1))
	max_chunk_len = request.form.get('max_chunk_len')
	max_chunk_len = int(max_chunk_len) if max_chunk_len else None
	selected_doc_ids = request.form.get('selected_doc_ids', '')
	submit_type = request.form.get('submit', 'selected')
	if submit_type == 'all':
		doc_ids = [f['doc_id'] for f in files]
	else:
		doc_ids = [d for d in selected_doc_ids.split(',') if d]
		if not doc_ids:
			flash('No documents selected for chunking.', 'warning')
			return redirect(url_for('step4_bp.step4_page'))
	summary = []
	preview_chunks = None
	for doc_id in doc_ids:
		file_info = next((f for f in files if f['doc_id'] == doc_id), None)
		if not file_info:
			continue
		doc_path = os.path.join(file_info['filename'])
		doc_path = os.path.join(file_info.get('dir', file_info.get('path', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step3', 'Clean-Results'))), file_info['filename'])
		t0 = time.time()
		try:
			chunks = headings_chunk(doc_path, mode, min_heading_gap, max_chunk_len)
			out_path = os.path.join(os.path.dirname(__file__), 'Chunked-by-Heading', f'{doc_id}.jsonl')
			params = {'mode': mode, 'min_heading_gap': min_heading_gap, 'max_chunk_len': max_chunk_len}
			write_jsonl(chunks, out_path, doc_id, 'heading', params)
			ms_elapsed = int((time.time() - t0) * 1000)
			write_log(doc_id, 'heading', len(chunks), ms_elapsed, params)
			summary.append(f'{doc_id}: {len(chunks)} chunks')
			preview_chunks = read_first_chunks(out_path, n=3)
		except Exception as e:
			flash(f'Error chunking {doc_id}: {e}', 'danger')
	flash(f'Chunked {len(doc_ids)} docs. ' + ', '.join(summary), 'success')
	return render_template('steps/step_4.html', files=files, preview_headings_chunks=preview_chunks, preview_token_chunks=None)

@step4_bp.route('/chunk_token', methods=['POST'])
def chunk_token():
	import time
	files = list_clean_files()
	window_size = int(request.form.get('window_size', 700))
	overlap = int(request.form.get('overlap', 150))
	tokenization = request.form.get('tokenization', 'whitespace_approx')
	selected_doc_ids = request.form.get('selected_doc_ids', '')
	submit_type = request.form.get('submit', 'selected')
	if submit_type == 'all':
		doc_ids = [f['doc_id'] for f in files]
	else:
		doc_ids = [d for d in selected_doc_ids.split(',') if d]
		if not doc_ids:
			flash('No documents selected for chunking.', 'warning')
			return redirect(url_for('step4_bp.step4_page'))
	summary = []
	preview_chunks = None
	for doc_id in doc_ids:
		file_info = next((f for f in files if f['doc_id'] == doc_id), None)
		if not file_info:
			continue
		doc_path = os.path.join(file_info['filename'])
		doc_path = os.path.join(file_info.get('dir', file_info.get('path', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'step3', 'Clean-Results'))), file_info['filename'])
		t0 = time.time()
		try:
			chunks = token_chunk(doc_path, window_size, overlap, tokenization)
			out_path = os.path.join(os.path.dirname(__file__), 'Chunked-by-Token', f'{doc_id}.jsonl')
			params = {'window_size': window_size, 'overlap': overlap, 'tokenization': tokenization}
			write_jsonl(chunks, out_path, doc_id, 'token', params)
			ms_elapsed = int((time.time() - t0) * 1000)
			write_log(doc_id, 'token', len(chunks), ms_elapsed, params)
			summary.append(f'{doc_id}: {len(chunks)} chunks')
			preview_chunks = read_first_chunks(out_path, n=3)
		except Exception as e:
			flash(f'Error chunking {doc_id}: {e}', 'danger')
	flash(f'Chunked {len(doc_ids)} docs. ' + ', '.join(summary), 'success')
	return render_template('steps/step_4.html', files=files, preview_headings_chunks=None, preview_token_chunks=preview_chunks)
