"""
Redis Synchronization Layer for Server Communication
Handles pub/sub messaging between servers
"""

import redis
import json
import threading
from typing import Callable, Dict
import logging

logger = logging.getLogger(__name__)

class RedisSyncManager:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.message_handlers: Dict[str, Callable] = {}
        self.listening = False
        self.listener_thread = None
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except redis.ConnectionError:
            logger.error("Failed to connect to Redis")
            raise
    
    def subscribe_to_channel(self, channel: str, handler: Callable[[dict], None]):
        """Subscribe to a Redis channel with a message handler."""
        self.message_handlers[channel] = handler
        self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")
    
    def publish_message(self, channel: str, message: dict):
        """Publish a message to a Redis channel."""
        try:
            message_str = json.dumps(message)
            self.redis_client.publish(channel, message_str)
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
    
    def start_listening(self):
        """Start listening for messages in a separate thread."""
        if self.listening:
            return
        
        self.listening = True
        self.listener_thread = threading.Thread(target=self._listen_for_messages)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        logger.info("Started Redis message listener")
    
    def stop_listening(self):
        """Stop listening for messages."""
        self.listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1)
        self.pubsub.close()
        logger.info("Stopped Redis message listener")
    
    def _listen_for_messages(self):
        """Internal method to listen for Redis pub/sub messages."""
        try:
            for message in self.pubsub.listen():
                if not self.listening:
                    break
                
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    try:
                        parsed_data = json.loads(data)
                        if channel in self.message_handlers:
                            self.message_handlers[channel](parsed_data)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse message from {channel}: {data}")
                    except Exception as e:
                        logger.error(f"Error handling message from {channel}: {e}")
        except Exception as e:
            logger.error(f"Error in Redis listener: {e}")
    
    def get_game_state(self, game_id: str = "default") -> dict:
        """Get the current game state from Redis."""
        state_key = f"game_state:{game_id}"
        state_str = self.redis_client.get(state_key)
        
        if state_str:
            return json.loads(state_str)
        return None
    
    def set_game_state(self, state: dict, game_id: str = "default"):
        """Store the current game state in Redis."""
        state_key = f"game_state:{game_id}"
        state_str = json.dumps(state)
        self.redis_client.set(state_key, state_str)
        logger.debug(f"Updated game state in Redis: {game_id}")
    
    def clear_game_state(self, game_id: str = "default"):
        """Clear the game state from Redis."""
        state_key = f"game_state:{game_id}"
        self.redis_client.delete(state_key)
        logger.info(f"Cleared game state: {game_id}")

# Channel names for different types of messages
CHANNELS = {
    'GAME_SYNC': 'tic_tac_toe:sync',
    'PLAYER_JOIN': 'tic_tac_toe:join',
    'PLAYER_LEAVE': 'tic_tac_toe:leave',
    'GAME_MOVE': 'tic_tac_toe:move',
    'GAME_RESET': 'tic_tac_toe:reset'
} 
