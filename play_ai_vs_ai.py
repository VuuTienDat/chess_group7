import pygame
import chess
from chess_game import ChessGame
from Engine.engine import Engine
from utils import (
    WIDTH, HEIGHT, screen, images, menu_background, game_font, sounds,
    draw_board, draw_pieces, draw_button
)
from notification import handle_move_outcome
import time

def play_ai_vs_ai():
    """Play a game between two AI players."""
    board = chess.Board()
    engine1 = Engine(max_depth=4, max_time=10.0)
    engine2 = Engine(max_depth=4, max_time=10.0)
    
    print("Starting AI vs AI game...")
    print("AI 1 (White) vs AI 2 (Black)")
    print("\nInitial position:")
    print(board)
    
    while not board.is_game_over():
        # Get the current engine based on turn
        current_engine = engine1 if board.turn == chess.WHITE else engine2
        current_engine.set_position(board.fen())
        
        # Get the best move
        move = current_engine.get_best_move()
        if not move:
            print("No legal moves available!")
            break
            
        # Convert move to UCI string
        uci_move = move.uci()
        
        # Get source and target squares
        from_square = chess.parse_square(uci_move[:2])
        to_square = chess.parse_square(uci_move[2:4])
        
        # Get source and target coordinates
        from_col = chess.square_file(from_square)
        from_row = chess.square_rank(from_square)
        to_col = chess.square_file(to_square)
        to_row = chess.square_rank(to_square)
        
        # Make the move
        board.push(move)
        
        # Print move information
        print(f"\n{'White' if board.turn == chess.BLACK else 'Black'} plays: {uci_move}")
        print(f"From: ({from_col}, {from_row})")
        print(f"To: ({to_col}, {to_row})")
        print("\nCurrent position:")
        print(board)
        
        # Add a small delay between moves
        time.sleep(1)
    
    # Print game result
    result = board.outcome()
    if result:
        if result.winner is None:
            print("\nGame ended in a draw!")
        else:
            print(f"\n{'White' if result.winner else 'Black'} wins by {result.termination.name}!")
    else:
        print("\nGame ended without a result.")