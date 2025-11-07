#!/bin/bash
# GairiHead Setup Script
# Run this on the Pi 5 to install dependencies

set -e

echo "========================================="
echo "GairiHead Setup"
echo "========================================="
echo

# Check if running on Pi 5
if ! grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: Not running on Raspberry Pi 5"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    pigpio \
    python3-pigpio \
    git \
    portaudio19-dev \
    libportaudio2 \
    libasound2-dev

# Enable and start pigpio daemon (needed for precise servo control)
echo "🔧 Enabling pigpio daemon..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
cd ~/GairiHead
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/faces
mkdir -p logs

# Set permissions
echo "🔧 Setting permissions..."
chmod +x tests/test_servos.py
chmod +x setup.sh

echo
echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source /Gary/GairiHead/venv/bin/activate"
echo
echo "2. Test servos (connect servos first!):"
echo "   python tests/test_servos.py"
echo
echo "3. Install Ollama for local LLM:"
echo "   curl -fsSL https://ollama.com/install.sh | sh"
echo "   ollama pull llama3.2:3b"
echo
echo "========================================="
