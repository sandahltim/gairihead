#!/usr/bin/env python3
"""
Test Voice Activity Detection (VAD) Recording

This script tests the new VAD-based recording that automatically stops
when the user finishes speaking (instead of fixed 3-second timeout).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
import numpy as np
from loguru import logger
from src.voice_handler import VoiceHandler

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

print("=" * 70)
print("VOICE ACTIVITY DETECTION (VAD) TEST")
print("=" * 70)
print("\nThis test demonstrates automatic recording stop when you finish speaking.")
print("No more fixed 3-second timeout!")
print("\n" + "=" * 70 + "\n")

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize voice handler
print("Initializing voice handler...")
handler = VoiceHandler(config)
print("\n" + "=" * 70)

# Test 1: VAD-based recording
print("\nTEST 1: VAD Recording (auto-stop when done speaking)")
print("=" * 70)
print("\nSpeak now... The recording will automatically stop when you're done.")
print("Maximum duration: 30 seconds")
print("Stops after: 1.5 seconds of silence")
print("\nStarting in 3... 2... 1...\n")

import time
time.sleep(3)

audio = handler.record_audio_with_vad(
    max_duration=30.0,
    silence_duration=1.5,
    vad_aggressiveness=2
)

if audio is not None:
    duration = len(audio) / handler.sample_rate
    rms = np.sqrt(np.mean(audio ** 2))
    print(f"\n✅ Recording successful!")
    print(f"   Duration: {duration:.1f}s")
    print(f"   RMS: {rms:.4f}")
    print(f"   Samples: {len(audio)}")
else:
    print("\n❌ Recording failed (no speech detected)")

# Test 2: Compare with fixed-duration recording
print("\n" + "=" * 70)
print("\nTEST 2: Fixed Duration Recording (old method for comparison)")
print("=" * 70)
print("\nSpeak for exactly 3 seconds... (will cut you off!)")
print("\nStarting in 3... 2... 1...\n")

time.sleep(3)

audio2 = handler.record_audio(duration=3.0)

if audio2 is not None:
    duration2 = len(audio2) / handler.sample_rate
    rms2 = np.sqrt(np.mean(audio2 ** 2))
    print(f"\n✅ Recording successful!")
    print(f"   Duration: {duration2:.1f}s (always exactly 3.0s)")
    print(f"   RMS: {rms2:.4f}")
    print(f"   Samples: {len(audio2)}")
else:
    print("\n❌ Recording failed")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nVAD Recording Benefits:")
print("  ✅ Stops automatically when you finish speaking")
print("  ✅ No more cut-off sentences")
print("  ✅ No awkward waiting for timeout")
print("  ✅ More natural user experience")
print("\nFixed Duration Recording Drawbacks:")
print("  ❌ Always records for exactly N seconds")
print("  ❌ Might cut you off mid-sentence")
print("  ❌ Or waste time waiting for timeout")
print("\n" + "=" * 70)
print("\nVAD is now enabled by default in GairiHead!")
print("Configure in config/gairi_head.yaml under 'voice.vad'")
print("\n" + "=" * 70)
