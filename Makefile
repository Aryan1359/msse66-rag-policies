eval-ask:
	@fuser -k 8000/tcp 2>/dev/null || pkill -f "python app.py" 2>/dev/null || true
	@python app.py & sleep 2
	@mkdir -p out
	@python scripts/eval_ask.py --server http://127.0.0.1:8000 --file data/eval/qa.jsonl > out/eval_ask.json || true
	@fuser -k 8000/tcp 2>/dev/null || pkill -f "python app.py" 2>/dev/null || true
	@echo "Summary:"
	@python -m scripts.print_eval_summary
