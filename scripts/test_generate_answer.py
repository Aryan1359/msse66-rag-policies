import json
from scripts.generate_answer import run
q = "What is the PTO accrual policy?"
res = run(q, topk=3)
print("Keys:", list(res.keys()))
print("Answer preview:", res["answer"][:140].replace("\n"," "))
print("Sources:", res["sources"][:2])
