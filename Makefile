.PHONY: eval-ask eval-gate

eval-ask:
	python scripts/eval_ask.py --limit 5

# CI Gate with default thresholds; override via env if desired
# MIN_GROUNDED=0.75 MIN_CITATION=0.75 P95_MS=4000 make eval-gate
eval-gate:
	python scripts/eval_ask.py \
		--min-grounded $${MIN_GROUNDED:-0.75} \
		--min-citation $${MIN_CITATION:-0.75} \
		--p95-total $${P95_MS:-4000} \
		--json-out data/eval/latest_metrics.json \
		--md-out data/eval/latest_metrics.md
eval-ask:
	@mkdir -p out
	@python scripts/eval_ask.py --inproc --file data/eval/qa.jsonl > out/eval_ask.json || true
	@echo "Summary:"
	@python -m scripts.print_eval_summary
