from Engine.board import Board
from Engine.engine import Engine

def main():
    board = Board()
    print("Initial board:")
    board.print_board()

    engine = Engine()

    while True:
        print("Your move (e.g., e2e4, or 'quit' to exit): ")
        move = input().strip()
        if move.lower() == "quit":
            break

        if len(move) != 4 or not move[0].isalpha() or not move[2].isalpha() or not move[1].isdigit() or not move[3].isdigit():
            print("Invalid move format! Use UCI notation (e.g., e2e4).")
            continue

        try:
            from_square = (8 - int(move[1]), ord(move[0]) - ord('a'))
            to_square = (8 - int(move[3]), ord(move[2]) - ord('a'))
            if not board.move(from_square, to_square):
                print("Invalid move! Try again.")
                continue
            print("Your move:")
            board.print_board()
        except (ValueError, IndexError) as e:
            print(f"Invalid move! Error: {e}")
            continue

        engine.set_position(board.get_fen())
        best_move = engine.get_best_move()
        if best_move:
            print(f"Engine moves: {best_move}")
            from_square = (8 - int(best_move[1]), ord(best_move[0]) - ord('a'))
            to_square = (8 - int(best_move[3]), ord(best_move[2]) - ord('a'))
            if not board.move(from_square, to_square):
                print("Engine made an invalid move! Exiting...")
                break
            print("Board after Engine's move:")
            board.print_board()
        else:
            print("Engine did not return a move. Exiting...")
            break

if __name__ == "__main__":
    main()