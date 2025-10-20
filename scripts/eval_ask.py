import requests, json, time, re, argparse

def load_qa(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", type=str, default="http://127.0.0.1:8000")
    ap.add_argument("--file", type=str, default="data/eval/qa.jsonl")
    ap.add_argument("--topk", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=10)
    args = ap.parse_args()
    qa = load_qa(args.file)
    rows = []
    for item in qa:
        qid = item["id"]
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        t0 = time.time()
        try:
            r = requests.post(f"{args.server}/ask", json={"question": question, "topk": args.topk}, timeout=args.timeout)
            elapsed = int((time.time() - t0) * 1000)
            data = r.json()
        except Exception as ex:
            rows.append({"id": qid, "error": str(ex)})
            continue
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        source_labels = data.get("source_labels", {})
        retrieval_ms = data.get("retrieval_ms", 0)
        llm_ms = data.get("llm_ms", 0)
        has_sources = len(sources) > 0
        citation_present = bool(re.search(r"\[S\d+\]", answer))
        citation_correct = (not citation_present) or (citation_present and has_sources)
        keyword_hit = any(kw.lower() in answer.lower() for kw in expected_keywords)
        rows.append({
            "id": qid,
            "has_sources": has_sources,
            "citation_present": citation_present,
            "citation_correct": citation_correct,
            "keyword_hit": keyword_hit,
            "retrieval_ms": retrieval_ms,
            "llm_ms": llm_ms,
            "total_ms": elapsed,
            "answer": answer,
            "sources": sources,
            "source_labels": source_labels
        })
    # Aggregates
    n = len(rows)
    summary = {
        "n": n,
        "grounded_rate": sum(r.get("has_sources", False) for r in rows) / n if n else 0,
        "citation_rate": sum(r.get("citation_present", False) for r in rows) / n if n else 0,
        "citation_correct_rate": sum(r.get("citation_correct", False) for r in rows) / n if n else 0,
        "keyword_hit_rate": sum(r.get("keyword_hit", False) for r in rows) / n if n else 0,
        "mean_retrieval_ms": int(sum(r.get("retrieval_ms", 0) for r in rows) / n) if n else 0,
        "mean_llm_ms": int(sum(r.get("llm_ms", 0) for r in rows) / n) if n else 0,
        "mean_total_ms": int(sum(r.get("total_ms", 0) for r in rows) / n) if n else 0,
    }
    out = {"rows": rows, "summary": summary}
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
