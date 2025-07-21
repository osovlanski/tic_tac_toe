# Real-Time Tic-Tac-Toe Over Two Servers

A real-time, multiplayer Tic-Tac-Toe game that allows two players to compete from separate clients connected to different backend servers. The servers synchronize game state in real-time using Redis pub/sub.

## 🏗️ Architecture and Communication Design

### System Architecture

```
┌─────────────┐    WebSocket    ┌──────────────┐    Redis     ┌──────────────┐    WebSocket    ┌─────────────┐
│   Client A  │ ←────────────→  │   Server A   │ ←─ pub/sub ─→ │   Server B   │ ←────────────→  │   Client B  │
│             │                 │   (port      │              │   (port      │                 │             │
│ CLI Player X│                 │    3001)     │              │    3002)     │                 │ CLI Player O│
└─────────────┘                 └──────────────┘              └──────────────┘                 └─────────────┘
                                        │                              │
                                        └──────── Redis Server ────────┘
                                              (Shared Game State)
```

### Communication Flow

1. **Client-Server Communication**: WebSocket connections for real-time bidirectional messaging
2. **Server-Server Synchronization**: Redis pub/sub channels for instant state synchronization
3. **State Persistence**: Game state stored in Redis for crash recovery and consistency
4. **Event Broadcasting**: All game events (moves, joins, leaves) broadcast across servers

### Key Components

- **GameState**: Core game logic, validation, and win detection
- **RedisSyncManager**: Handles cross-server communication via Redis pub/sub
- **WebSocket Servers**: Independent servers that can handle clients
- **CLI Client**: Terminal-based interface with ASCII board display

### Message Protocol

The system uses JSON messages over WebSocket:

**Client → Server:**
```json
{ "type": "join" }
{ "type": "move", "row": 1, "col": 2 }
{ "type": "reset" }
```

**Server → Client:**
```json
{ "type": "joined", "playerId": "X", "message": "You are player X" }
{ "type": "update", "board": [["X","",""],["","O",""],["","",""]], "nextTurn": "X" }
{ "type": "win", "winner": "O" }
{ "type": "error", "message": "Invalid move" }
```

## 📋 Prerequisites

- Python 3.7+
- Redis Server
- Terminal/Command Line access

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/osovlanski/tic_tac_toe.git
   cd tic_tac_toe
   ```

2. **Install Redis:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   
   # Windows: Download from https://redis.io/download
   ```

3. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

## 🖥️ Running the Servers

### 1. Start Redis Server
```bash
# Start Redis (keep running in background)
redis-server
```

### 2. Start Server A (Terminal 1)
```bash
python3 websocket_server.py --server-id A --port 3001 --force-reset
```

### 3. Start Server B (Terminal 2)
```bash
python3 websocket_server.py --server-id B --port 3002 --force-reset
```

You should see output like:
```
INFO - Starting Tic-Tac-Toe server A on port 3001
INFO - Connected to Redis successfully
INFO - Subscribed to channel: tic_tac_toe:sync
INFO - Server A running on ws://localhost:3001
```

Note: the force-reset parameter is for reset and create new game. 
without it if a game already exist we can't add more playrs

## 🎮 Running CLI Clients

### Client 1 - Connect to Server A (Terminal 3)
```bash
python3 cli_client.py --server localhost:3001
```

### Client 2 - Connect to Server B (Terminal 4)
```bash
python3 cli_client.py --server localhost:3002
```

### Client Commands
Once connected, use these commands:
- `move <row> <col>` - Make a move (e.g., `move 1 2`)
- `help` - Show available commands
- `board` - Display current game board
- `reset` - Reset the game
- `quit` - Exit the client

### Board Coordinates
The game board uses 0-based indexing:
```
   0   1   2
0    |   |  
  -----------
1    |   |  
  -----------
2    |   |  
```

## 🧪 Testing 2-Player Game

### Complete Test Setup

1. **Open 4 terminals** and navigate to the project directory in each

2. **Terminal 1 - Start Redis:**
   ```bash
   redis-server
   ```

3. **Terminal 2 - Start Server A:**
   ```bash
   python3 websocket_server.py --server-id A --port 3001
   ```

4. **Terminal 3 - Start Server B:**
   ```bash
   python3 websocket_server.py --server-id B --port 3002
   ```

5. **Terminal 4 - Start Client 1 (Player X):**
   ```bash
   python3 cli_client.py --server localhost:3001
   ```

6. **Terminal 5 - Start Client 2 (Player O):**
   ```bash
   python3 cli_client.py --server localhost:3002
   ```

### Example Game Session

**Client 1 (Player X on Server A):**
```
> move 1 1    # Place X in center
🎯 Move sent: (1, 1)
```

**Client 2 (Player O on Server B):**
```
# Board automatically updates to show X's move
> move 0 0    # Place O in top-left
🎯 Move sent: (0, 0)
```

**Both clients will see:**
```
   0   1   2
0  O |   |  
  -----------
1    | X |  
  -----------
2    |   |  
```

### Test Scenarios

1. **Basic Cross-Server Play**: Players on different servers making moves
2. **Server Restart**: Stop one server mid-game, restart it, game continues
3. **Invalid Moves**: Try occupied cells, wrong turns, out-of-bounds
4. **Win Detection**: Get three in a row to test win conditions
5. **Connection Issues**: Disconnect a client and reconnect

## 🛠️ Development and AI Usage Notes

### AI-Generated Components

This project was developed with significant assistance from AI (Claude). Here are the details:

#### Initial AI Prompt:
"create a real-time multiplayer Tic-Tac-Toe game with two independent WebSocket servers that synchronize via Redis. 
Players should be able to connect to either server and play against each other in real-time with a CLI interface."

"add to project settings file for local env running and a standart .gitignore file for python project"

"add testing file to validate code logic"

#### AI-Generated Code Areas:

1. **Game Logic (`game_state.py`)** - *Fully AI-generated*
   - Core game mechanics and validation
   - Win/draw detection algorithms
   - Player management system

2. **Redis Synchronization (`redis_sync.py`)** - *Fully AI-generated*
   - Pub/sub message handling
   - Cross-server communication protocol
   - State persistence mechanisms

3. **WebSocket Server (`websocket_server.py`)** - *Fully AI-generated*
   - Async WebSocket handling
   - Message routing and validation
   - Client connection management
   - Redis integration

4. **CLI Client (`cli_client.py`)** - *Fully AI-generated*
   - Terminal-based user interface
   - ASCII board rendering
   - Real-time message handling
   - User input processing

#### Manual Improvements Made:

1. **Error Handling Enhancement**:
   - Added more robust connection error handling
   - Improved Redis connection failure recovery
   - Better client disconnection cleanup

2. **User Experience Improvements**:
   - Enhanced CLI interface with emojis and clear formatting
   - Added more descriptive error messages
   - Improved help system and command validation

3. **Code Organization**:
   - Added comprehensive docstrings
   - Improved variable naming and code structure
   - Added logging for better debugging

4. **Protocol Refinements**:
   - Standardized JSON message formats
   - Added message validation
   - Improved state synchronization logic

#### Follow-up AI Prompts Used:
- "Add better error handling for Redis connection failures"
- "Improve the CLI interface with better user feedback"
- "Add comprehensive documentation and setup instructions"
- "Create a setup script for easy deployment"

### Code Quality Notes

- **Modularity**: Clean separation of concerns across different modules
- **Error Handling**: Comprehensive error handling and recovery
- **Documentation**: Extensive inline documentation and README
- **Testing**: Multiple test scenarios for validation
- **Maintainability**: Clear code structure and consistent patterns

## 🚨 Troubleshooting

### Common Issues

**Redis Connection Failed:**
```bash
# Check if Redis is running
redis-cli ping
# Should return "PONG"

# Start Redis if not running
redis-server
```

**Port Already in Use:**
```bash
# Find process using port
lsof -i :3001
# Kill the process if needed
kill -9 <PID>
```

**WebSocket Connection Issues:**
```bash
# Check if server is running
netstat -an | grep 3001
# Should show LISTEN state
```

**Client Commands Not Working:**
- Use exact format: `move 0 1` (not `move 0,1`)
- Coordinates must be 0-2
- Only make moves when it's your turn

## 📁 Project Structure

```
tic_tac_toe/
├── game_state.py          # Core game logic
├── redis_sync.py          # Server synchronization
├── websocket_server.py    # WebSocket server implementation
├── cli_client.py          # Terminal client interface
├── requirements.txt       # Python dependencies
├── setup.sh              # Automated setup script
└── README.md             # This documentation
```

## 🔧 Technical Details

- **WebSocket Library**: `websockets` for async communication
- **Redis Client**: `redis-py` for pub/sub messaging
- **Concurrency**: Asyncio for handling multiple connections
- **Protocol**: JSON over WebSocket for structured communication
- **State Management**: Redis for persistent, synchronized game state

## 🎯 Future Enhancements

- Multiple concurrent games support
- Web-based client interface
- Player authentication and accounts
- Game statistics and history
- Tournament/bracket system
- Spectator mode

## 📄 License

This project is provided as-is for educational and demonstration purposes.
