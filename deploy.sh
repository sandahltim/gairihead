#!/bin/bash
# Deploy GairiHead to Pi 5
# Usage: ./deploy.sh [pi_host]

PI_HOST="${1:-tim@100.103.67.41}"
REMOTE_DIR="/home/tim/GairiHead"

echo "========================================="
echo "Deploying GairiHead to Pi 5"
echo "Target: $PI_HOST"
echo "========================================="
echo

# Create remote directory
echo "📁 Creating remote directory..."
ssh $PI_HOST "mkdir -p $REMOTE_DIR"

# Copy project files
echo "📦 Copying files..."
rsync -av --exclude='venv' \
          --exclude='*.pyc' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='*.log' \
          /Gary/GairiHead/ $PI_HOST:$REMOTE_DIR/

echo
echo "✅ Deployment complete!"
echo
echo "Next steps:"
echo "1. SSH to Pi 5:"
echo "   ssh $PI_HOST"
echo
echo "2. Run setup:"
echo "   cd $REMOTE_DIR"
echo "   ./setup.sh"
echo
echo "3. Test servos:"
echo "   source venv/bin/activate"
echo "   python tests/test_servos.py"
echo
echo "========================================="
