#!/bin/bash
# Restart GairiHead (stop then start)

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Stop GairiHead
$SCRIPT_DIR/stop_gairihead.sh

# Wait a moment
sleep 2

# Start GairiHead
$SCRIPT_DIR/start_gairihead.sh
