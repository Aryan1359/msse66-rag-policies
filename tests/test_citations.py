import app, json

def test_citations_map():
    c = app.app.test_client()
    r = c.post("/ask", json={"question":"PTO accrual policy?", "topk":3})
    assert r.status_code == 200
    data = r.get_json()
    assert "sources" in data and "source_labels" in data
    # source_labels keys must be sequential S1..Sk matching len(sources)
    k = len(data["sources"])
    assert list(data["source_labels"].keys()) == [f"S{i}" for i in range(1, k+1)]
