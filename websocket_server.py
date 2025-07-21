"""
WebSocket Server Implementation
Handles client connections and game logic coordination
"""

import asyncio
import websockets
import json
import logging
import argparse
import uuid
from typing import Dict, Set
from game_state import GameState, GameStatus, Player
from redis_sync import RedisSyncManager, CHANNELS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TicTacToeServer:
    def __init__(self, server_id: str, port: int, force_reset: bool = False):
        self.server_id = server_id
        self.port = port
        self.force_reset = force_reset
        self.clients: Dict[websockets.WebSocketServerProtocol, str] = {}  # websocket -> player_id
        self.game_state = GameState()
        self.redis_sync = RedisSyncManager()
        
        # Subscribe to Redis channels
        self.redis_sync.subscribe_to_channel(CHANNELS['GAME_SYNC'], self.handle_game_sync)
        self.redis_sync.subscribe_to_channel(CHANNELS['PLAYER_JOIN'], self.handle_player_join_sync)
        self.redis_sync.subscribe_to_channel(CHANNELS['PLAYER_LEAVE'], self.handle_player_leave_sync)
        self.redis_sync.subscribe_to_channel(CHANNELS['GAME_MOVE'], self.handle_game_move_sync)
        self.redis_sync.subscribe_to_channel(CHANNELS['GAME_RESET'], self.handle_game_reset_sync)
        
        # Start Redis listener
        self.redis_sync.start_listening()
        
        # Load or reset game state
        self.load_game_state()
    
    def load_game_state(self):
        """Load game state from Redis on server startup or reset if forced."""
        if self.force_reset:
            logger.info("Forcing game state reset")
            self.game_state.reset()
            self.save_game_state()
            return

        saved_state = self.redis_sync.get_game_state()
        if saved_state:
            self.game_state.load_state(saved_state)
            logger.info(f"Loaded game state from Redis: {saved_state}")
        else:
            logger.info("No saved game state found, starting fresh")
            self.game_state.reset()
            self.save_game_state()
    
    def save_game_state(self):
        """Save current game state to Redis."""
        state_dict = self.game_state.get_state_dict()
        self.redis_sync.set_game_state(state_dict)
    # 
    async def register_client(self, websocket):
        """Register a new client connection."""
        player_id = str(uuid.uuid4())
        self.clients[websocket] = player_id
        logger.info(f"Client {player_id} connected to server {self.server_id}")
        
        # Send current game state to new client
        await self.send_game_update(websocket)
        
        return player_id
    
    async def unregister_client(self, websocket):
        """Unregister a client connection."""
        if websocket in self.clients:
            player_id = self.clients[websocket]
            del self.clients[websocket]
            
            # Remove player from game
            self.game_state.remove_player(player_id)
            self.save_game_state()
            
            # Notify other servers
            self.redis_sync.publish_message(CHANNELS['PLAYER_LEAVE'], {
                'server_id': self.server_id,
                'player_id': player_id
            })
            
            # Broadcast game state update
            await self.broadcast_game_state()
            
            logger.info(f"Client {player_id} disconnected from server {self.server_id}")
    
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message from client."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            player_id = self.clients[websocket]

            print (f"🔄 Received message from {player_id}: {data}")
            
            if message_type == 'join':
                await self.handle_join(websocket, player_id, data)
            elif message_type == 'move':
                await self.handle_move(websocket, player_id, data)
            elif message_type == 'reset':
                await self.handle_reset(websocket, player_id)
            else:
                await self.send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, "Internal server error")
    
    async def handle_join(self, websocket, player_id, data):
        """Handle player join request."""
        # First load latest state from Redis to ensure we have current player count
        saved_state = self.redis_sync.get_game_state()
        if saved_state:
            self.game_state.load_state(saved_state)
    
        assigned_player = self.game_state.add_player(player_id)
        
        if assigned_player is None:
            # Game is full, send error
            logger.warning(f"Player {player_id} tried to join but game is full")
            await self.send_error(websocket, "Game is full")
            return
        
        # Save state and notify other servers
        self.save_game_state()
        self.redis_sync.publish_message(CHANNELS['PLAYER_JOIN'], {
            'server_id': self.server_id,
            'player_id': player_id,
            'player_symbol': assigned_player.value,
            'game_state': self.game_state.get_state_dict()  # Include full game state
        })
        
        # Send join confirmation
        await websocket.send(json.dumps({
            'type': 'joined',
            'playerId': assigned_player.value,
            'message': f'You are player {assigned_player.value}'
        }))
        
        # Broadcast updated game state to all clients
        await self.broadcast_game_state()
        
        logger.info(f"Player {player_id} joined as {assigned_player.value}")
    
    async def handle_move(self, websocket, player_id, data):
        """Handle a move from a client."""
        try:
            row = data.get('row')
            col = data.get('col')
            
            success, message = self.game_state.make_move(player_id, row, col)
            
            if success:
                # Save state to Redis
                self.save_game_state()
                
                # Notify other servers about the move
                self.redis_sync.publish_message(CHANNELS['GAME_MOVE'], {
                    'server_id': self.server_id,
                    'player_id': player_id,
                    'row': row,
                    'col': col,
                    'game_state': self.game_state.get_state_dict()
                })
                
                # Broadcast updated state to ALL clients
                await self.broadcast_game_state()
                
                logger.info(f"Move by {player_id} at ({row}, {col}) processed successfully")
            else:
                await self.send_error(websocket, message)
                
        except Exception as e:
            logger.error(f"Error processing move: {e}")
            await self.send_error(websocket, "Error processing move")
    
    async def handle_reset(self, websocket, player_id):
        print (f"🔄 Player {player_id} requested game reset")

        """Handle game reset request."""
        self.game_state.reset()
        self.save_game_state()
        
        # Notify other servers
        self.redis_sync.publish_message(CHANNELS['GAME_RESET'], {
            'server_id': self.server_id,
            'player_id': player_id
        })
        
        await self.broadcast_game_state()
        logger.info(f"Game reset by player {player_id}")
    
    async def send_game_update(self, websocket):
        """Send current game state to a specific client."""
        state_dict = self.game_state.get_state_dict()
        message = {
            'type': 'update',
            'board': state_dict['board'],
            'nextTurn': state_dict['current_turn'],
            'status': state_dict['status'],
            'playerCount': state_dict['player_count']
        }
        await websocket.send(json.dumps(message))
    
    async def broadcast_game_state(self):
        """Broadcast current game state to all connected clients."""
        state_dict = self.game_state.get_state_dict()
        logger.info(f"Broadcasting game state: {state_dict}")
        
        message = {
            'type': 'update',
            'board': state_dict['board'],
            'nextTurn': state_dict['current_turn'],
            'status': state_dict['status'],
            'playerCount': state_dict['player_count'],
            'players': state_dict['players']  # Include full players info
        }
        
        await self.broadcast_message(message)
        logger.info("Game state broadcast complete")
    
    async def broadcast_message(self, message):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
        
        message_str = json.dumps(message)
        disconnected_clients = []
        
        for websocket in self.clients:
            try:
                await websocket.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            await self.unregister_client(websocket)
    
    async def send_error(self, websocket, error_message):
        """Send error message to client."""
        message = {
            'type': 'error',
            'message': error_message
        }
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    # Redis synchronization handlers
    def handle_game_sync(self, data):
        """Handle game state synchronization from other servers."""
        if data.get('server_id') != self.server_id:
            # Update from another server
            self.load_game_state()
            asyncio.create_task(self.broadcast_game_state())
    
    def handle_player_join_sync(self, data):
        """Handle player join sync from other servers."""
        if data.get('server_id') != self.server_id:
            # Get the full game state from the message
            if 'game_state' in data:
                self.game_state.load_state(data['game_state'])
            else:
                # Fallback to loading from Redis
                self.load_game_state()
        
            # Ensure we broadcast the update to our clients 
            asyncio.create_task(self.broadcast_game_state())
    
    def handle_player_leave_sync(self, data):
        """Handle player leave sync from other servers."""
        if data.get('server_id') != self.server_id:
            self.load_game_state()
            asyncio.create_task(self.broadcast_game_state())
    
    def handle_game_move_sync(self, data):
        """Handle game move sync from other servers."""
        if data.get('server_id') != self.server_id:
            logger.info(f"Received move sync from server {data.get('server_id')}")
            
            # Update game state from the received state
            if 'game_state' in data:
                self.game_state.load_state(data['game_state'])
                # Ensure local clients are updated
                asyncio.create_task(self.broadcast_game_state())
                logger.info("Game state updated from move sync")
    
    def handle_game_reset_sync(self, data):
        """Handle game reset sync from other servers."""
        if data.get('server_id') != self.server_id:
            self.load_game_state()
            asyncio.create_task(self.broadcast_game_state())
    
    async def client_handler(self, websocket, path):
        """Handle new WebSocket client connections."""
        player_id = await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting Tic-Tac-Toe server {self.server_id} on port {self.port}")
        
        start_server = websockets.serve(
            self.client_handler,
            "localhost",
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        asyncio.get_event_loop().run_until_complete(start_server)
        logger.info(f"Server {self.server_id} running on ws://localhost:{self.port}")
        
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logger.info(f"Server {self.server_id} shutting down...")
        finally:
            self.redis_sync.stop_listening()

def main():
    parser = argparse.ArgumentParser(description='Tic-Tac-Toe WebSocket Server')
    parser.add_argument('--server-id', required=True, help='Server identifier (A or B)')
    parser.add_argument('--port', type=int, required=True, help='Server port')
    parser.add_argument('--force-reset', action='store_true', 
                       help='Force reset the game state on startup')
    
    args = parser.parse_args()
    
    server = TicTacToeServer(args.server_id, args.port, args.force_reset)
    server.start_server()

if __name__ == "__main__":
    main()