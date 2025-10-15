import argparse, json, sys
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_JSONL = Path("data/index/policies.jsonl")
EMB_NPY = Path("data/index/policies.npy")
META_JSON = Path("data/index/meta.json")

def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def load_index():
    if not (EMB_NPY.exists() and META_JSON.exists() and INDEX_JSONL.exists()):
        print("[ERR] Missing index files. Run scripts/index_jsonl.py and scripts/embed_index.py first.", file=sys.stderr)
        sys.exit(1)
    mat = np.load(EMB_NPY)               # [N, D], L2-normalized rows
    meta = json.load(open(META_JSON, "r", encoding="utf-8"))
    recs = list(read_jsonl(INDEX_JSONL)) # original chunks to preview text
    return mat, meta, recs

def l2_normalize(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec) + 1e-12
    return (vec / n).astype(np.float32)

def search(query:str, topk:int):
    mat, meta, recs = load_index()
    model = SentenceTransformer(meta["model_name"], device="cpu")
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=False)[0].astype(np.float32)
    q = l2_normalize(q)
    # cosine because both sides L2-normalized
    scores = mat @ q
    # argpartition is faster than full sort for large N; N is small so either is fine
    idx = np.argsort(-scores)[:topk]
    id_map = meta["id_map"]
    hits = []
    for i in idx:
        m = id_map[i]
        # find the original record by id (small corpora -> linear scan OK)
        # r["id"] is like "doc::chunk-#"
        r = next((r for r in recs if r.get("id")==m["id"]), None)
        preview = (r.get("text","")[:160].replace("\n"," ") + "…") if r else ""
        hits.append({
            "rank": len(hits)+1,
            "score": float(scores[i]),
            "doc_id": m.get("doc_id"),
            "chunk_id": m.get("chunk_id"),
            "id": m.get("id"),
            "preview": preview
        })
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="search query text")
    ap.add_argument("--topk", type=int, default=3)
    args = ap.parse_args()
    hits = search(args.query, args.topk)
    print(json.dumps({"query": args.query, "topk": args.topk, "results": hits}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
