from pathlib import Path
import subprocess, sys
import os
from .services_rag import _embeddings_dir

def ensure_embeddings(method: str = "headings", model: str = "minilm") -> Path:
    folder = _embeddings_dir() / f"{method}__minilm"
    vec = folder / "vectors.npy"
    meta = folder / "meta.json"
    if vec.exists() and meta.exists():
        return folder
    # run embed script to build on the fly (CPU safe)
    cmd = [sys.executable, "scripts/embed_index.py", "--method", method, "--model", model]
    subprocess.check_call(cmd, env=os.environ.copy())
    return folder
