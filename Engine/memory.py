import json
from pathlib import Path

MEMORY_FILE = Path("Engine/knowledge.json")

def load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def remember(fen, result):
    data = load_memory()
    if fen not in data:
        data[fen] = {"wins": 0, "losses": 0, "draws": 0}
    if result == "win":
        data[fen]["wins"] += 1
    elif result == "loss":
        data[fen]["losses"] += 1
    else:
        data[fen]["draws"] += 1
    save_memory(data)
