import json, sys, pathlib

def main():
    path = pathlib.Path("out/eval_ask.json")
    if not path.exists():
        print("ERROR: out/eval_ask.json not found", file=sys.stderr)
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    print(data.get("summary", data))

if __name__ == "__main__":
    main()
