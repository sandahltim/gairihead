#!/bin/bash
# Download Piper TTS voice models
# Voice models are too large for git (60-115MB each)

VOICE_DIR="/home/tim/GairiHead/data/piper_voices"
mkdir -p "$VOICE_DIR"

echo "=================================================================="
echo "DOWNLOADING PIPER TTS VOICE MODELS"
echo "=================================================================="
echo ""
echo "Downloading 3 male voice options (~220MB total)..."
echo ""

cd "$VOICE_DIR" || exit 1

# Joe - Smooth, warm male (SELECTED DEFAULT)
echo "1/3: Downloading Joe (smooth, warm) - 61MB..."
wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium.onnx.json

# Lessac - Professional, clear male
echo "2/3: Downloading Lessac (professional, clear) - 61MB..."
wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Ryan - Casual, conversational male
echo "3/3: Downloading Ryan (casual, conversational) - 116MB..."
wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx.json

echo ""
echo "=================================================================="
echo "✅ DOWNLOAD COMPLETE"
echo "=================================================================="
echo ""
echo "Downloaded voices:"
ls -lh "$VOICE_DIR"/*.onnx
echo ""
echo "To change voice, edit config/gairi_head.yaml:"
echo "  voice: 'joe'     # (default) Smooth, warm"
echo "  voice: 'lessac'  # Professional, clear"
echo "  voice: 'ryan'    # Casual, conversational"
echo ""
