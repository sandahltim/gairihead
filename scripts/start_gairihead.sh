#!/bin/bash
# GairiHead Startup Script
# Starts both the main app and the remote control server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Log directory
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   GairiHead Voice Assistant${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if already running
if [ -f "$PROJECT_DIR/.gairihead.pid" ]; then
    PID=$(cat "$PROJECT_DIR/.gairihead.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  GairiHead is already running (PID: $PID)${NC}"
        echo -e "Use: ${GREEN}./scripts/stop_gairihead.sh${NC} to stop it first"
        exit 1
    else
        # Stale PID file
        rm -f "$PROJECT_DIR/.gairihead.pid"
        rm -f "$PROJECT_DIR/.gairihead_server.pid"
    fi
fi

# Start GairiHead Server (port 8766 - Gary can control GairiHead)
echo -e "${GREEN}Starting GairiHead Server (port 8766)...${NC}"
nohup python3 src/gairi_head_server.py \
    > "$LOG_DIR/gairihead_server.log" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PROJECT_DIR/.gairihead_server.pid"

# Give server time to start
sleep 2

# Check if server started successfully
if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ GairiHead Server failed to start${NC}"
    echo -e "Check logs: ${YELLOW}$LOG_DIR/gairihead_server.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ GairiHead Server started (PID: $SERVER_PID)${NC}"

# Start GairiHead Main App (production mode - touchscreen)
echo -e "${GREEN}Starting GairiHead Main App (production mode)...${NC}"
nohup python3 main.py --mode production \
    > "$LOG_DIR/gairihead_main.log" 2>&1 &
MAIN_PID=$!
echo $MAIN_PID > "$PROJECT_DIR/.gairihead.pid"

# Give main app time to start
sleep 2

# Check if main app started successfully
if ! ps -p $MAIN_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ GairiHead Main App failed to start${NC}"
    echo -e "Check logs: ${YELLOW}$LOG_DIR/gairihead_main.log${NC}"

    # Kill server if main failed
    echo -e "Stopping server..."
    kill $SERVER_PID 2>/dev/null || true
    rm -f "$PROJECT_DIR/.gairihead.pid"
    rm -f "$PROJECT_DIR/.gairihead_server.pid"
    exit 1
fi

echo -e "${GREEN}✅ GairiHead Main App started (PID: $MAIN_PID)${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ GairiHead is running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Server PID:   ${GREEN}$SERVER_PID${NC} (port 8766)"
echo -e "Main App PID: ${GREEN}$MAIN_PID${NC} (touchscreen)"
echo ""
echo -e "Logs:"
echo -e "  Server: ${YELLOW}$LOG_DIR/gairihead_server.log${NC}"
echo -e "  Main:   ${YELLOW}$LOG_DIR/gairihead_main.log${NC}"
echo ""
echo -e "Commands:"
echo -e "  Status: ${GREEN}./scripts/status_gairihead.sh${NC}"
echo -e "  Logs:   ${GREEN}tail -f logs/gairihead_main.log${NC}"
echo -e "  Stop:   ${GREEN}./scripts/stop_gairihead.sh${NC}"
echo ""
