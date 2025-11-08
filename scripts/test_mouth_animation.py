#!/usr/bin/env python3
"""
Test Mouth Animation During Speech

Tests the mouth servo animation that syncs with TTS speech
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from src.servo_controller import ServoController
from src.voice_handler import VoiceHandler
from src.expression_engine import ExpressionEngine
import yaml

print("="*70)
print("MOUTH ANIMATION TEST")
print("="*70)

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print("\n1. Initializing servo controller...")
servo = ServoController(str(config_path))
print("   ✅ Servos initialized")

print("\n2. Initializing expression engine...")
expression = ExpressionEngine()
expression.set_controllers(servo_controller=servo)
print("   ✅ Expression engine initialized")

print("\n3. Initializing voice handler...")
voice = VoiceHandler(
    config=config,
    expression_engine=expression
)
print("   ✅ Voice handler initialized")

print("\n4. Testing mouth animation without speech...")
print("   Starting animation for 3 seconds...")
servo.start_speech_animation(base_amplitude=0.4)
time.sleep(3)
servo.stop_speech_animation()
print("   ✅ Animation test complete")

print("\n5. Testing mouth animation with TTS speech...")
test_phrases = [
    "Hello, I am Gary. This is a test of my mouth animation.",
    "The mouth should move in sync with my speech.",
    "Let's see how natural this looks!"
]

for i, phrase in enumerate(test_phrases, 1):
    print(f"\n   Test {i}/{len(test_phrases)}: \"{phrase[:40]}...\"")
    voice.speak(phrase)
    time.sleep(0.5)

print("\n6. Cleanup...")
servo.cleanup()
print("   ✅ Servos cleaned up")

print("\n" + "="*70)
print("✅ MOUTH ANIMATION TEST COMPLETE")
print("="*70)
print("\nDid the mouth animate naturally during speech?")
print("If not, adjust base_amplitude in voice_handler.py (line 370)")
print("Current amplitude: 0.4 (range: 0.0 - 1.0)")
print("="*70)
