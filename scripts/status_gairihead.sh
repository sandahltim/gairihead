#!/bin/bash
# Check GairiHead status

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   GairiHead Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

MAIN_RUNNING=false
SERVER_RUNNING=false

# Check main app
if [ -f "$PROJECT_DIR/.gairihead.pid" ]; then
    MAIN_PID=$(cat "$PROJECT_DIR/.gairihead.pid")

    if ps -p $MAIN_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Main App:${NC} Running (PID: $MAIN_PID)"
        MAIN_RUNNING=true

        # Get memory and CPU usage
        MEM=$(ps -o rss= -p $MAIN_PID | awk '{printf "%.1f MB", $1/1024}')
        CPU=$(ps -o %cpu= -p $MAIN_PID | awk '{printf "%.1f%%", $1}')
        echo -e "   Memory: $MEM | CPU: $CPU"
    else
        echo -e "${RED}❌ Main App:${NC} Not running (stale PID: $MAIN_PID)"
    fi
else
    echo -e "${RED}❌ Main App:${NC} Not running"
fi

# Check server
if [ -f "$PROJECT_DIR/.gairihead_server.pid" ]; then
    SERVER_PID=$(cat "$PROJECT_DIR/.gairihead_server.pid")

    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server:${NC} Running (PID: $SERVER_PID)"
        SERVER_RUNNING=true

        # Get memory and CPU usage
        MEM=$(ps -o rss= -p $SERVER_PID | awk '{printf "%.1f MB", $1/1024}')
        CPU=$(ps -o %cpu= -p $SERVER_PID | awk '{printf "%.1f%%", $1}')
        echo -e "   Memory: $MEM | CPU: $CPU"
    else
        echo -e "${RED}❌ Server:${NC} Not running (stale PID: $SERVER_PID)"
    fi
else
    echo -e "${RED}❌ Server:${NC} Not running"
fi

echo ""

# Overall status
if $MAIN_RUNNING && $SERVER_RUNNING; then
    echo -e "${GREEN}✅ GairiHead is fully operational${NC}"
elif $MAIN_RUNNING || $SERVER_RUNNING; then
    echo -e "${YELLOW}⚠️  GairiHead is partially running${NC}"
    if ! $MAIN_RUNNING; then
        echo -e "   Main App needs to be started"
    fi
    if ! $SERVER_RUNNING; then
        echo -e "   Server needs to be started"
    fi
else
    echo -e "${RED}❌ GairiHead is not running${NC}"
    echo -e "   Start with: ${GREEN}./scripts/start_gairihead.sh${NC}"
fi

echo ""

# Show log files
if [ -d "$PROJECT_DIR/logs" ]; then
    echo -e "${BLUE}Recent Logs:${NC}"
    echo -e "${YELLOW}Main App:${NC}"
    tail -5 "$PROJECT_DIR/logs/gairihead_main.log" 2>/dev/null || echo "   No logs yet"
    echo ""
    echo -e "${YELLOW}Server:${NC}"
    tail -5 "$PROJECT_DIR/logs/gairihead_server.log" 2>/dev/null || echo "   No logs yet"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
