#!/bin/bash
# Stop GairiHead (both server and main app)

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
echo -e "${BLUE}   Stopping GairiHead${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop main app
if [ -f "$PROJECT_DIR/.gairihead.pid" ]; then
    MAIN_PID=$(cat "$PROJECT_DIR/.gairihead.pid")
    echo -e "Stopping Main App (PID: $MAIN_PID)..."

    if ps -p $MAIN_PID > /dev/null 2>&1; then
        kill $MAIN_PID

        # Wait for graceful shutdown
        for i in {1..5}; do
            if ! ps -p $MAIN_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p $MAIN_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Force killing Main App...${NC}"
            kill -9 $MAIN_PID 2>/dev/null || true
        fi

        echo -e "${GREEN}✅ Main App stopped${NC}"
    else
        echo -e "${YELLOW}Main App not running${NC}"
    fi

    rm -f "$PROJECT_DIR/.gairihead.pid"
else
    echo -e "${YELLOW}No Main App PID file found${NC}"
fi

# Stop server
if [ -f "$PROJECT_DIR/.gairihead_server.pid" ]; then
    SERVER_PID=$(cat "$PROJECT_DIR/.gairihead_server.pid")
    echo -e "Stopping Server (PID: $SERVER_PID)..."

    if ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID

        # Wait for graceful shutdown
        for i in {1..5}; do
            if ! ps -p $SERVER_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Force killing Server...${NC}"
            kill -9 $SERVER_PID 2>/dev/null || true
        fi

        echo -e "${GREEN}✅ Server stopped${NC}"
    else
        echo -e "${YELLOW}Server not running${NC}"
    fi

    rm -f "$PROJECT_DIR/.gairihead_server.pid"
else
    echo -e "${YELLOW}No Server PID file found${NC}"
fi

echo ""
echo -e "${GREEN}✅ GairiHead stopped${NC}"
echo ""
