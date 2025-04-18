import json
from pathlib import Path

MEMORY_FILE = Path("Engine/knowledge.json")

#def load_memory():
#    if MEMORY_FILE.exists():
#        with open(MEMORY_FILE, "r") as f:
#            return json.load(f)
#    return {}

#def save_memory(data):
#   with open(MEMORY_FILE, "w") as f:
#        json.dump(data, f, indent=2)

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

def save_memory(fen, best_move):
    """
    Lưu trạng thái FEN và nước đi (dạng UCI) vào file memory.json.
    Nếu file chưa tồn tại, tạo mới.
    
    Tham số:
      fen (str): Trạng thái FEN của bàn cờ.
      best_move (chess.Move): Nước đi mà AI đã chọn, sẽ được chuyển về dạng UCI.
    """
    memory_file = "memory.json"

    # Tải dữ liệu đã có
    try:
        with open(memory_file, "r") as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = {}

    # Lưu trạng thái FEN và nước đi tương ứng (convert move về UCI string)
    memory[fen] = best_move.uci()

    # Ghi lại dữ liệu vào file memory.json
    with open(memory_file, "w") as f:
        json.dump(memory, f, indent=4)

def load_memory():
    """
    Tải dữ liệu từ file memory.json.
    
    Trả về:
      dict: Bản đồ {FEN: best_move_uci, ...}
    """
    memory_file = "memory.json"
    try:
        with open(memory_file, "r") as f:
            memory = json.load(f)
        return memory
    except FileNotFoundError:
        return {}
    