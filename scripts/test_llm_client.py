from scripts.llm_client import generate_answer, is_configured, LLMNotConfigured

print("Configured?", is_configured())
try:
    if is_configured():
        out = generate_answer("Say 'test' and nothing else.")
        print("LLM OK:", out["text"][:20])
    else:
        raise LLMNotConfigured()
except LLMNotConfigured:
    print("LLM not configured (OK)")
