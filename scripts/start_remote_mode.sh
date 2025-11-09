#!/bin/bash
# Start GairiHead in REMOTE MODE (server only - for Gary control)
# Use this when Gary wants full remote control (speak + expressions)
# Use start_gairihead.sh for local button-press mode

cd "$(dirname "$0")/.."

echo "========================================"
echo "   GairiHead Remote Mode"
echo "========================================"
echo ""
echo "Starting server-only mode for Gary remote control..."
echo ""

# Stop main app if running
if [ -f pids/gairihead_main.pid ]; then
    MAIN_PID=$(cat pids/gairihead_main.pid)
    if ps -p $MAIN_PID > /dev/null 2>&1; then
        echo "Stopping local main app (PID: $MAIN_PID)..."
        kill $MAIN_PID
        sleep 1
    fi
fi

# Start server (or restart if already running)
./scripts/stop_gairihead.sh > /dev/null 2>&1
sleep 1

echo "Starting GairiHead Server (port 8766)..."
source venv/bin/activate
nohup python3 src/gairi_head_server.py > logs/gairihead_server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > pids/gairihead_server.pid

sleep 2

if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✅ GairiHead Server started (PID: $SERVER_PID)"
else
    echo "❌ Server failed to start"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ Remote Mode Active"
echo "========================================"
echo ""
echo "Gary can now control GairiHead via WebSocket (ws://100.103.67.41:8766)"
echo ""
echo "Available commands:"
echo "  - speak: Make GairiHead talk with mouth animation"
echo "  - set_expression: Control facial servos"
echo "  - capture_snapshot: Get camera image"
echo "  - record_audio: Record microphone"
echo "  - analyze_scene: Camera + face detection"
echo "  - get_status: Check hardware status"
echo ""
echo "To return to local mode: ./scripts/start_gairihead.sh"
echo "To stop: ./scripts/stop_gairihead.sh"
echo ""
