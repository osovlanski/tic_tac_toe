#!/bin/bash

# Tic-Tac-Toe Game Setup and Run Script

echo "🎮 Tic-Tac-Toe Real-Time Game Setup"
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed."
    exit 1
fi

# Check if Redis is installed and running
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Redis is not installed. Please install Redis first:"
    echo "   Ubuntu/Debian: sudo apt-get install redis-server"
    echo "   macOS: brew install redis"
    echo "   Windows: Download from https://redis.io/download"
    exit 1
fi

# Check if Redis is running
if ! pgrep redis-server > /dev/null; then
    echo "🚀 Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
    
    if ! pgrep redis-server > /dev/null; then
        echo "❌ Failed to start Redis. Please start it manually:"
        echo "   redis-server"
        exit 1
    fi
    echo "✅ Redis server started successfully"
else
    echo "✅ Redis server is already running"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    pip3 install websockets==11.0.3 redis==5.0.1
fi

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🎯 Setup Complete!"
echo ""
echo "To run the game:"
echo "=================="
echo ""
echo "1. Start Server A (Terminal 1):"
echo "   python3 websocket_server.py --server-id A --port 3001"
echo ""
echo "2. Start Server B (Terminal 2):"
echo "   python3 websocket_server.py --server-id B --port 3002"
echo ""
echo "3. Start Client 1 (Terminal 3):"
echo "   python3 cli_client.py --server localhost:3001"
echo ""
echo "4. Start Client 2 (Terminal 4):"
echo "   python3 cli_client.py --server localhost:3002"
echo ""
echo "🎮 Game Commands:"
echo "================="
echo "  move <row> <col> - Make a move (e.g., 'move 1 2')"
echo "  help            - Show help"
echo "  board           - Show current board"
echo "  reset           - Reset the game"
echo "  quit            - Exit client"
echo ""
echo "📝 Notes:"
echo "========="
echo "- Players can connect to different servers"
echo "- Game state syncs in real-time between servers"
echo "- Redis handles the synchronization"
echo "- Board coordinates are 0-2 for rows and columns" 
