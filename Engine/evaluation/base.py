from abc import ABC, abstractmethod
import chess

class BaseEvaluator(ABC):
    """Base class for all evaluators."""
    
    @abstractmethod
    def evaluate(self, board: chess.Board) -> int:
        """Evaluate the given board position."""
        pass 