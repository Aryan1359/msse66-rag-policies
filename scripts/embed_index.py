import json, os, sys, math
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_JSONL = Path("data/index/policies.jsonl")
OUT_DIR = Path("data/index")
EMB_NPY = OUT_DIR / "policies.npy"
META_JSON = OUT_DIR / "meta.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def l2_normalize(mat: np.ndarray) -> np.ndarray:
    # avoid divide-by-zero
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return (mat / norms).astype(np.float32)

def main():
    if not INDEX_JSONL.exists():
        print(f"[ERR] Missing {INDEX_JSONL}. Run scripts/index_jsonl.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Loading chunks from {INDEX_JSONL} ...")
    records = list(read_jsonl(INDEX_JSONL))
    if not records:
        print("[ERR] No records found in JSONL.")
        sys.exit(1)

    # Expect fields: id, doc_id, chunk_id, text (your index_jsonl.py format)
    texts = []
    id_map = []  # parallel to embeddings rows: list of {"id","doc_id","chunk_id"}
    for r in records:
        text = r.get("text", "").strip()
        if not text:
            continue
        texts.append(text)
        id_map.append({
            "id": r.get("id"),
            "doc_id": r.get("doc_id"),
            "chunk_id": r.get("chunk_id"),
        })

    print(f"[INFO] Loaded {len(texts)} chunks to embed.")
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    print(f"[INFO] Model loaded: {MODEL_NAME}")

    # Batch encode for stability on small machines
    batch_size = 64
    embs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        vecs = model.encode(
            batch,
            batch_size=len(batch),
            convert_to_numpy=True,
            normalize_embeddings=False,  # we'll normalize ourselves
            show_progress_bar=False,
        )
        embs.append(vecs.astype(np.float32))
        if (i // batch_size) % 10 == 0:
            print(f"[INFO] Embedded {min(i+batch_size, len(texts))}/{len(texts)}")

    mat = np.vstack(embs)
    mat = l2_normalize(mat)  # cosine via dot product later
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMB_NPY, mat)

    meta = {
        "model_name": MODEL_NAME,
        "rows": int(mat.shape[0]),
        "dim": int(mat.shape[1]),
        "source_index": str(INDEX_JSONL),
        "embeddings_file": str(EMB_NPY),
        "id_map": id_map,  # small corpora -> OK; if huge, we’d shard
    }
    with META_JSON.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved embeddings to {EMB_NPY} with shape {mat.shape}")
    print(f"[OK] Wrote metadata to {META_JSON}")

if __name__ == "__main__":
    main()
