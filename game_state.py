"""
Game State Manager for Tic-Tac-Toe
Handles game logic, validation, and win detection
"""

from typing import List, Optional, Tuple, Dict
from enum import Enum

class GameStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Player(Enum):
    X = "X"
    O = "O"

class GameState:
    def __init__(self):
        self.board: List[List[str]] = [["" for _ in range(3)] for _ in range(3)]
        self.current_turn: Player = Player.X
        self.status: GameStatus = GameStatus.WAITING
        self.winner: Optional[Player] = None
        self.players: Dict[str, Player] = {}  # player_id -> Player
        self.player_count: int = 0
        self.board_size: int = 3  # Tic-Tac-Toe is always 3x3
    
    def add_player(self, player_id: str) -> Optional[Player]:
        """Add a player to the game. Returns assigned player symbol or None if game is full."""
        if self.player_count >= 2:
            return None
        
        if self.player_count == 0:
            assigned_player = Player.X
        else:
            assigned_player = Player.O
            
        self.players[player_id] = assigned_player
        self.player_count += 1
        
        if self.player_count == 2:
            self.status = GameStatus.IN_PROGRESS
            
        return assigned_player
    
    def remove_player(self, player_id: str):
        """Remove a player from the game."""
        if player_id in self.players:
            del self.players[player_id]
            self.player_count -= 1
            if self.player_count < 2:
                self.status = GameStatus.WAITING
    
    def make_move(self, player_id: str, row: int, col: int) -> Tuple[bool, str]:
        """
        Attempt to make a move. Returns (success, message).
        """
        # Validate game state
        if self.status != GameStatus.IN_PROGRESS:
            return False, "Game is not in progress"
        
        # Validate player
        if player_id not in self.players:
            return False, "Player not in game"
        
        player = self.players[player_id]
        
        # Check if it's player's turn
        if player != self.current_turn:
            return False, f"Not your turn. Current turn: {self.current_turn.value}"
        
        # Validate move coordinates
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return False, "Invalid coordinates. Use 0-2 for row and column"
        
        # Check if cell is empty
        if self.board[row][col] != "":
            return False, "Cell is already occupied"
        
        # Make the move
        self.board[row][col] = player.value
        
        # Check for win or draw
        if self._check_win():
            self.winner = player
            self.status = GameStatus.FINISHED
        elif self._is_board_full():
            self.status = GameStatus.FINISHED
            self.winner = None  # Draw
        else:
            # Switch turns
            self.current_turn = Player.O if self.current_turn == Player.X else Player.X
        
        return True, "Move successful"
    
    def _check_win(self) -> bool:
        """Check if there's a winner."""
        board = self.board
        
        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != "":
                return True
        
        # Check columns
        for col in range(self.board_size):
            if board[0][col] == board[1][col] == board[2][col] != "":
                return True
        
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != "":
            return True
        if board[0][2] == board[1][1] == board[2][0] != "":
            return True
        
        return False
    
    def _is_board_full(self) -> bool:
        """Check if the board is full."""
        for row in self.board:
            for cell in row:
                if cell == "":
                    return False
        return True
    
    def get_state_dict(self) -> dict:
        """Get the current game state as a dictionary."""
        return {
            "board": self.board,
            "current_turn": self.current_turn.value if self.current_turn else None,
            "status": self.status.value,
            "winner": self.winner.value if self.winner else None,
            "player_count": self.player_count
        }
    
    def reset(self):
        """Reset the game to initial state."""
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.current_turn = Player.X
        self.status = GameStatus.WAITING if self.player_count < 2 else GameStatus.IN_PROGRESS
        self.winner = None 
