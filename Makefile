eval-ask:
	@mkdir -p out
	@python scripts/eval_ask.py --inproc --file data/eval/qa.jsonl > out/eval_ask.json || true
	@echo "Summary:"
	@python -m scripts.print_eval_summary
