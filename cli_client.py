"""
CLI WebSocket Client for Tic-Tac-Toe Game
Provides terminal-based interface for playing the game
"""

import asyncio
import websockets
import json
import threading
import sys
import argparse
from typing import Optional

class TicTacToeClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.player_id: Optional[str] = None
        self.game_board = [["" for _ in range(3)] for _ in range(3)]
        self.game_status = "waiting"
        self.current_turn = None
        self.player_count = 0
        self.connected = False
        self.input_thread = None
        self.loop = asyncio.get_event_loop()
        
    def display_board(self):
        """Display the current game board in ASCII format."""
        print("\n" + "="*20)
        print("   TIC-TAC-TOE")
        print("="*20)
        print("\nCurrent Board:")
        print("   0   1   2")
        for i, row in enumerate(self.game_board):
            row_display = f"{i}  "
            for j, cell in enumerate(row):
                display_cell = cell if cell else " "
                row_display += f" {display_cell} "
                if j < 2:
                    row_display += "|"
            print(row_display)
            if i < 2:
                print("  -----------")
        
        print(f"\nGame Status: {self.game_status}")
        if self.current_turn:
            print(f"Current Turn: {self.current_turn}")
        print(f"Players Connected: {self.player_count}/2")
        
        if self.player_id:
            print(f"You are: {self.player_id}")
        
        if self.game_status == "in_progress":
            if self.current_turn == self.player_id:
                print("\n🎮 It's your turn! Enter your move.")
            else:
                print(f"\n⏳ Waiting for {self.current_turn}'s move...")
        elif self.game_status == "waiting":
            print("\n⏳ Waiting for another player to join...")
        
        print("\n" + "="*20)
    
    def display_help(self):
        """Display help information."""
        print("\n" + "="*40)
        print("            HELP - HOW TO PLAY")
        print("="*40)
        print("Commands:")
        print("  move <row> <col> - Make a move (e.g., 'move 1 2')")
        print("  help            - Show this help message")
        print("  quit            - Quit the game")
        print("  reset           - Reset the game (if you're a player)")
        print("  board           - Show current board")
        print("\nBoard coordinates:")
        print("  Rows and columns are numbered 0, 1, 2")
        print("  Top-left is (0,0), bottom-right is (2,2)")
        print("\nExample moves:")
        print("  move 0 0  - Place in top-left")
        print("  move 1 1  - Place in center")
        print("  move 2 2  - Place in bottom-right")
        print("="*40)
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            print(f"Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            print("✅ Connected successfully!")
            
            # Join the game
            await self.send_message({"type": "join"})
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
        
        return True
    
    async def disconnect(self):
        """Disconnect from the server."""
        self.connected = False
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from server.")
    
    async def send_message(self, message: dict):
        """Send a message to the server."""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"❌ Failed to send message: {e}")
                self.connected = False
    
    async def handle_server_message(self, message: str):
        """Handle incoming message from server."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'joined':
                self.player_id = data.get('playerId')
                print(f"✅ {data.get('message', 'Joined game successfully!')}")
                self.display_board()
                
            elif message_type == 'update':
                self.game_board = data.get('board', self.game_board)
                self.current_turn = data.get('nextTurn')
                self.game_status = data.get('status', 'waiting')
                self.player_count = data.get('playerCount', 0)
                self.display_board()
                
            elif message_type == 'win':
                winner = data.get('winner')
                print(f"\n🎉 Game Over! Winner: {winner}")
                if winner == self.player_id:
                    print("🏆 Congratulations! You won!")
                else:
                    print("😢 Better luck next time!")
                self.display_board()
                
            elif message_type == 'draw':
                print(f"\n🤝 Game Over! It's a draw!")
                self.display_board()
                
            elif message_type == 'error':
                error_message = data.get('message', 'Unknown error')
                print(f"❌ Error: {error_message}")
                
            else:
                print(f"📨 Server message: {data}")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid message from server: {message}")
        except Exception as e:
            print(f"❌ Error handling server message: {e}")
    
    async def listen_for_messages(self):
        """Listen for messages from the server."""
        try:
            async for message in self.websocket:
                await self.handle_server_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("❌ Connection to server lost.")
            self.connected = False
        except Exception as e:
            print(f"❌ Error listening for messages: {e}")
            self.connected = False
    
    def handle_user_input(self):
        """Handle user input in a separate thread."""
        self.display_help()
        print("\nType 'help' for commands or 'quit' to exit.")
        
        while self.connected:
            try:
                user_input = input("\n> ").strip().lower()
                
                if not user_input:
                    continue
                
                if user_input == 'quit':
                    print("Goodbye! 👋")
                    self.connected = False
                    break
                
                elif user_input == 'help':
                    self.display_help()
                
                elif user_input == 'board':
                    self.display_board()
                
                elif user_input == 'reset':
                    if self.player_id:
                        asyncio.run_coroutine_threadsafe(self.send_message({"type": "reset"}), self.loop)
                        print("🔄 Reset request sent...")
                    else:
                        print("❌ You must join the game first!")
                
                elif user_input.startswith('move '):
                    parts = user_input.split()
                    if len(parts) == 3:
                        try:
                            row = int(parts[1])
                            col = int(parts[2])
                            
                            if 0 <= row <= 2 and 0 <= col <= 2:
                                message = {
                                    "type": "move",
                                    "row": row,
                                    "col": col
                                }
                                asyncio.run_coroutine_threadsafe(self.send_message(message), self.loop)
                                print(f"🎯 Move sent: ({row}, {col})")
                            else:
                                print("❌ Invalid coordinates! Use 0-2 for row and column.")
                        except ValueError:
                            print("❌ Invalid move format! Use: move <row> <col>")
                    else:
                        print("❌ Invalid move format! Use: move <row> <col>")
                
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye! 👋")
                self.connected = False
                break
            except Exception as e:
                print(f"❌ Error handling input: {e}")
    
    async def run(self):
        """Main client run loop."""
        if not await self.connect():
            return
        
        # Start input handling in a separate thread
        self.input_thread = threading.Thread(target=self.handle_user_input)
        self.input_thread.daemon = True
        self.input_thread.start()
        
        # Listen for server messages
        await self.listen_for_messages()
        
        # Clean up
        await self.disconnect()
        
        # Wait for input thread to finish
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1)

def main():
    """Main function to run the client."""
    parser = argparse.ArgumentParser(description='Tic-Tac-Toe CLI Client')
    parser.add_argument('--server', default='localhost:3001', 
                       help='Server address (default: localhost:3001)')
    
    args = parser.parse_args()
    
    # Parse server address
    if ':' in args.server:
        host, port = args.server.split(':')
        server_url = f"ws://{host}:{port}"
    else:
        server_url = f"ws://{args.server}:3001"
    
    print("🎮 Tic-Tac-Toe CLI Client")
    print("=" * 30)
    
    client = TicTacToeClient(server_url)
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\nClient interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"❌ Client error: {e}")

if __name__ == "__main__":
    main()