import chess
import chess.engine
import os
from Engine.engine import Engine  # Đảm bảo bạn có lớp Engine trong engine.py

# ==== CẤU HÌNH ====
STOCKFISH_PATH = "C:/Users/VUONG/TTNT7.2/Engine/stockfish/stockfish.exe"
STOCKFISH_ELO = 1320  # Mức độ "yếu" của Stockfish để bot dễ test hơn
STOCKFISH_DEPTH = 1  # Giới hạn độ sâu tính toán của Stockfish
BOT_DEPTH = 3        # Độ sâu của bot
NUM_GAMES = 10       # Số ván để đánh giá
SHOW_MOVES = False   # In ra từng nước đi

# ==== KIỂM TRA FILE ====
if not os.path.exists(STOCKFISH_PATH):
    raise FileNotFoundError(f"Không tìm thấy Stockfish tại: {STOCKFISH_PATH}")

# ==== HÀM CHƠI 1 VÁN ====
def play_game(bot_as_white=True, bot_depth=5, stockfish_elo=1350, show_moves=True):
    board = chess.Board()
    bot = Engine(depth=bot_depth)

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as stockfish:
        stockfish.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": stockfish_elo
        })

        move_count = 1
        while not board.is_game_over():
            is_bot_turn = (board.turn == chess.WHITE and bot_as_white) or (board.turn == chess.BLACK and not bot_as_white)
            
            if is_bot_turn:
                # BOT ĐI
                try:
                    bot.set_position(board.fen())
                    move_uci = bot.get_best_move()
                    if move_uci is None:
                        print("❌ Bot không có nước đi!")
                        break
                    move = chess.Move.from_uci(move_uci)
                    if move not in board.legal_moves:
                        print(f"❌ Nước đi bot không hợp lệ: {move_uci}")
                        break
                    board.push(move)
                    if show_moves:
                        print(f"{move_count}. 🤖 Bot đi: {move_uci}")
                except Exception as e:
                    print(f"❌ Lỗi khi bot đi: {e}")
                    break
            else:
                # STOCKFISH ĐI
                try:
                    result = stockfish.play(board, chess.engine.Limit(depth=STOCKFISH_DEPTH))
                    board.push(result.move)
                    if show_moves:
                        print(f"{move_count}. 🐟 Stockfish đi: {result.move.uci()}")
                except Exception as e:
                    print(f"❌ Lỗi khi Stockfish đi: {e}")
                    break

            if show_moves:
                print(board, "\n")
            move_count += 1

        return board.result()

# ==== HÀM ĐÁNH GIÁ BOT ====
def evaluate_bot(num_games=10, bot_depth=4, stockfish_elo=800):
    wins = 0
    draws = 0
    losses = 0

    for i in range(num_games):
        bot_as_white = (i % 2 == 0)
        print(f"\n🔁 Ván {i + 1}/{num_games} | Bot chơi {'Trắng' if bot_as_white else 'Đen'}")
        result = play_game(bot_as_white=bot_as_white, bot_depth=bot_depth, stockfish_elo=stockfish_elo, show_moves=SHOW_MOVES)

        if result == "1-0":
            if bot_as_white:
                wins += 1
                print("✅ Bot thắng (Trắng)")
            else:
                losses += 1
                print("❌ Bot thua (Đen)")
        elif result == "0-1":
            if bot_as_white:
                losses += 1
                print("❌ Bot thua (Trắng)")
            else:
                wins += 1
                print("✅ Bot thắng (Đen)")
        else:
            draws += 1
            print("🤝 Hòa")

    # ==== TỔNG KẾT ====
    print("\n📊 --- Tổng kết ---")
    print(f"Thắng: {wins}, Hòa: {draws}, Thua: {losses}")
    score = (wins + 0.5 * draws) / num_games
    print(f"Tỷ lệ hiệu suất: {score * 100:.1f}%")

    if score in [0, 1]:
        print("⚠️ Không thể ước lượng ELO (toàn thắng hoặc toàn thua).")
    else:
        elo_diff = -400 * (score - 0.5) / (0.5 - score)
        print(f"📈 Ước lượng chênh lệch ELO so với Stockfish Elo {stockfish_elo}: ~{int(elo_diff)}")

# ==== CHẠY CHÍNH ====
if __name__ == "__main__":
    evaluate_bot(num_games=NUM_GAMES, bot_depth=BOT_DEPTH, stockfish_elo=STOCKFISH_ELO)
