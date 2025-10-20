import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RAG_MODEL = os.getenv("RAG_MODEL", "llama-3.1-8b-instruct")
RAG_MAX_TOKENS = int(os.getenv("RAG_MAX_TOKENS", "512"))

class LLMNotConfigured(Exception):
    pass

def is_configured() -> bool:
    return bool(GROQ_API_KEY)

def generate_answer(prompt: str) -> dict:
    """
    Returns {"text": str, "model": str, "tokens": int}.
    Raises LLMNotConfigured if no API key is present.
    System prompt enforces grounded, citation-first behavior (actual citations will be passed in the user prompt by the caller in later steps).
    """
    if not GROQ_API_KEY:
        raise LLMNotConfigured("No GROQ_API_KEY in environment.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    body = {
        "model": RAG_MODEL,
        "max_tokens": RAG_MAX_TOKENS,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful RAG answerer. Only use the provided policy excerpts. "
                    "Always include numbered source markers like [S1], [S2] that the caller provides. "
                    "If the question is out of scope or unsupported by the excerpts, say so explicitly."
                )
            },
            {"role": "user", "content": prompt}
        ]
    }

    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"text": text, "model": RAG_MODEL, "tokens": usage.get("total_tokens", 0)}
