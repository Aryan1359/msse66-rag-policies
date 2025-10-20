import app

def test_ask_smoke():
    client = app.app.test_client()
    r = client.post("/ask", json={"question":"PTO accrual?", "topk":2})
    assert r.status_code == 200
    data = r.get_json()
    for k in ["question","answer","sources","source_labels","retrieval_ms","llm_ms","model","tokens"]:
        assert k in data
