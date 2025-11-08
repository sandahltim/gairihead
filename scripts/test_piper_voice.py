#!/usr/bin/env python3
"""
Test Piper TTS - much more natural than espeak
"""

import sys
import wave
from pathlib import Path

# Add piper to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from piper import PiperVoice
import subprocess

# Test phrase
test_phrase = "Sarcasm setting at seventy-five percent. How can I help you today?"

print("="*70)
print("PIPER TTS TEST - Natural Neural Voice")
print("="*70)
print(f"\nTest phrase: \"{test_phrase}\"")
print("\nThis uses neural TTS - much more natural than espeak!")
print("="*70 + "\n")

# Voice model path
voice_model = "/home/tim/GairiHead/data/piper_voices/en_US-lessac-medium.onnx"

print(f"Loading voice model: {voice_model}")
voice = PiperVoice.load(voice_model)

# Synthesize to WAV file
output_file = "/tmp/piper_test.wav"
print(f"\n🔊 Speaking with Piper...")

with wave.open(output_file, 'wb') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(voice.config.sample_rate)
    voice.synthesize(test_phrase, wav_file)

print(f"✅ Audio generated: {output_file}")

# Play the audio
print("▶️  Playing audio...\n")
subprocess.run(['aplay', '-D', 'plughw:0,0', output_file])

print("\n" + "="*70)
print("How does it sound?")
print("="*70)
print("\nPiper is MUCH more natural than espeak!")
print("This is the same voice quality you'll get in GairiHead.")
print("\nTo use Piper:")
print("  1. It's already installed ✅")
print("  2. Voice model downloaded ✅")
print("  3. Just needs integration into voice_handler")
print("\n" + "="*70)
