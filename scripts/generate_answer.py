
import os, sys
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
            from scripts.search_jsonl import search as kw_search
            hits = kw_search(query, topk=topk)
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
    out.sort(key=lambda x: -x["score"])
    import sys
    print(f"[retrieval] mode={mode} hits={len(out)}", file=sys.stderr)
    return out[:topk]

# --- Prompt builder ---
def build_prompt(question: str, chunks: list) -> str:
    lines = [
        "You are answering strictly from the provided policy excerpts.",
        "Include inline citations using [S1], [S2], ... matching the numbered sources below.",
        "If the answer is not supported by the sources, say it is not supported.",
        f"Question: {question}",
        "Sources:"
    ]
    for idx, c in enumerate(chunks, 1):
        snippet = c["text"].replace("\n", " ").strip()
        snippet = snippet[:180] + ("…" if len(snippet) > 180 else "")
        lines.append(f"S{idx} (doc_id:{c['doc_id']}, chunk_id:{c['chunk_id']}): {snippet}")
    lines.append("Answer succinctly (3–7 sentences), citing like [S1], [S3].")
    return "\n".join(lines)

# --- Synthesis ---
def synthesize(question: str, chunks: list):
    from scripts.llm_client import generate_answer, is_configured, LLMNotConfigured
    prompt = build_prompt(question, chunks)
    if is_configured():
        t0 = time.time()
        try:
            out = generate_answer(prompt)
            llm_ms = int((time.time() - t0) * 1000)
            return out["text"], {"model": out["model"], "tokens": out["tokens"], "llm_ms": llm_ms}
        except Exception as ex:
            # fallback to extractive
            pass
    # fallback: extractive summary
    snippets = [c["text"].strip().replace("\n", " ") for c in chunks[:3] if c.get("text") and str(c["text"]).strip()]
    if snippets:
        answer = " ".join(snippets)
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
    out = {
        "question": question,
        "answer": answer,
        "sources": [
            {"doc_id": c["doc_id"], "chunk_id": c["chunk_id"], "score": c["score"]}
            for c in chunks
        ],
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
