
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import time
import json
import argparse
import sys

# --- Retrieval ---
def retrieve(query: str, topk: int = 4) -> list:
    mode = os.getenv("RETRIEVAL_MODE", "keyword").lower()
    out = []
    if mode == "vector":
        try:
            from scripts.vector_search import search as vector_search
            hits = vector_search(query, topk=topk)
            for h in hits:
                t = h.get("text") or h.get("chunk") or h.get("content") or h.get("snippet")
                if t is not None and str(t).strip():
                    out.append({
                        "doc_id": h.get("doc_id"),
                        "chunk_id": h.get("chunk_id"),
                        "text": str(t).strip(),
                        "score": float(h.get("score", 0)),
                    })
        except Exception:
            pass
    elif mode == "http":
        try:
            import httpx
            url = f"http://127.0.0.1:8000/search?q={query}&topk={topk}&mode=vector"
            r = httpx.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            results = data.get("results")
            if results is None and isinstance(data, list):
                results = data
            elif results is None:
                results = []
            for h in results:
                t = h.get("text") or h.get("chunk") or h.get("content") or h.get("snippet") or h.get("preview")
                if t is not None and str(t).strip():
                    out.append({
                        "doc_id": h.get("doc_id"),
                        "chunk_id": h.get("chunk_id"),
                        "text": str(t).strip(),
                        "score": float(h.get("score", 0)),
                    })
        except Exception:
            pass
    else:  # keyword (default)
        try:
            from scripts.search_jsonl import search as kw_search, load_index
            index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "index", "policies.jsonl")
            from pathlib import Path
            recs = load_index(Path(index_path))
            hits = kw_search(recs, query, topk=topk)
            for h in hits:
                t = h.get("text") or h.get("chunk") or h.get("content") or h.get("snippet")
                if t is not None and str(t).strip():
                    out.append({
                        "doc_id": h.get("doc_id"),
                        "chunk_id": h.get("chunk_id"),
                        "text": str(t).strip(),
                        "score": float(h.get("score", 0)),
                    })
        except Exception:
            pass
    # Only keep non-empty text, sort by score descending, and return topk
    out = [x for x in out if x.get("text") and str(x["text"]).strip()]
    out.sort(key=lambda x: -x["score"])
    import sys
    print(f"[retrieval] mode={mode} hits={len(out)}", file=sys.stderr)
    return out[:topk]

# --- Prompt builder ---
def build_prompt(question: str, chunks: list) -> str:
    lines = [
        "You are answering strictly from the provided policy excerpts.",
        "Always cite using [S1], [S2], ... matching the numbered sources below. Do not invent citations.",
        "If the answer is not supported by the sources, say it is not supported.",
        f"Question: {question}",
        "Sources:"
    ]
    for idx, c in enumerate(chunks, 1):
        snippet = c["text"].replace("\n", " ").strip()
        snippet = snippet[:180] + ("…" if len(snippet) > 180 else "")
        lines.append(f"S{idx} (doc_id:{c['doc_id']}, chunk_id:{c['chunk_id']}): {snippet}")
    lines.append("Answer concisely (3–5 sentences), always citing like [S1], [S2].")
    return "\n".join(lines)

# --- Synthesis ---
def synthesize(question: str, chunks: list):
    from scripts.llm_client import generate_answer, is_configured, LLMNotConfigured
    import re
    prompt = build_prompt(question, chunks)
    if is_configured():
        t0 = time.time()
        try:
            out = generate_answer(prompt)
            llm_ms = int((time.time() - t0) * 1000)
            answer = out["text"]
            # If answer has no [S#] and we had sources, append [S1]
            if chunks and not re.search(r"\[S\d+\]", answer):
                answer = answer.rstrip() + " [S1]"
            # Trim to ~1200 chars, preserve citations
            if len(answer) > 1200:
                # Try to trim at a sentence boundary if possible
                trimmed = answer[:1200]
                last_period = trimmed.rfind('.')
                if last_period > 900:
                    answer = trimmed[:last_period+1]
                else:
                    answer = trimmed
            return answer, {"model": out["model"], "tokens": out["tokens"], "llm_ms": llm_ms}
        except Exception as ex:
            pass
    # fallback: extractive summary
    snippets = [c["text"].strip().replace("\n", " ") for c in chunks[:3] if c.get("text") and str(c["text"]).strip()]
    if snippets:
        # Try to join into 3–5 sentences
        answer = " ".join(snippets)
        # Truncate to ~3–5 sentences (split by period)
        sentences = re.split(r'(?<=[.!?]) +', answer)
        answer = " ".join(sentences[:5])
        answer += "\n\n(LLM disabled; extractive summary)"
    else:
        answer = "No relevant policy excerpts found. (LLM disabled; extractive summary)"
    return answer, {"model": "disabled", "tokens": 0, "llm_ms": 0}

# --- Main run ---
def run(question: str, topk: int = 4):
    t0 = time.time()
    chunks = retrieve(question, topk=topk)
    retrieval_ms = int((time.time() - t0) * 1000)
    answer, meta = synthesize(question, chunks)
    # Build source_labels: {"S1":{doc_id,chunk_id}, ...} in same order as sources
    source_labels = {f"S{i+1}": {"doc_id": c["doc_id"], "chunk_id": c["chunk_id"]} for i, c in enumerate(chunks)}
    out = {
        "question": question,
        "answer": answer,
        "sources": [
            {"doc_id": c["doc_id"], "chunk_id": c["chunk_id"], "score": c["score"]}
            for c in chunks
        ],
        "source_labels": source_labels,
        "retrieval_ms": retrieval_ms,
        "llm_ms": meta.get("llm_ms", 0),
        "model": meta.get("model", ""),
        "tokens": meta.get("tokens", 0),
    }
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--q", "--question", dest="question", required=True)
    parser.add_argument("--topk", type=int, default=4)
    parser.add_argument("--dump", type=str, default=None)
    args = parser.parse_args()
    res = run(args.question, topk=args.topk)
    print(json.dumps(res, indent=None))
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
