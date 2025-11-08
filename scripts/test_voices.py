#!/usr/bin/env python3
"""
Test different TTS voices to find the right balance
Less robotic but still has character
"""

import pyttsx3
import time

# Test phrase (TARS-style)
test_phrase = "Sarcasm setting at seventy-five percent. How can I help you today?"

# Voice options to test (English voices with different characteristics)
voice_options = [
    {"id": "gmw/en", "name": "British English (current)", "rate": 150},
    {"id": "gmw/en-us", "name": "American English", "rate": 150},
    {"id": "gmw/en-gb-x-rp", "name": "British RP (formal)", "rate": 150},
    {"id": "gmw/en-gb-scotland", "name": "Scottish English", "rate": 150},
    {"id": "gmw/en-us", "name": "American English (slower)", "rate": 130},
    {"id": "gmw/en-us", "name": "American English (faster)", "rate": 170},
    {"id": "gmw/en", "name": "British English (slower)", "rate": 130},
]

print("="*70)
print("GAIRI VOICE TEST")
print("="*70)
print(f"\nTest phrase: \"{test_phrase}\"")
print("\nListening to different voice options...")
print("="*70 + "\n")

# Create engine ONCE (pyttsx3 doesn't like multiple init/destroy cycles)
engine = pyttsx3.init()
engine.setProperty('volume', 0.8)

for i, option in enumerate(voice_options, 1):
    print(f"{i}. Testing: {option['name']} @ {option['rate']} WPM")

    # Change properties on existing engine
    engine.setProperty('voice', option['id'])
    engine.setProperty('rate', option['rate'])

    print(f"   🔊 Speaking...")
    engine.say(test_phrase)
    engine.runAndWait()

    time.sleep(0.5)  # Short pause between voices
    print()

print("="*70)
print("Which voice sounds best?")
print("="*70)
print("\nRecommendations:")
print("- Less robotic: American English @ 130-150 WPM")
print("- Character but smooth: British English @ 130 WPM")
print("- TARS-like: British RP @ 150 WPM")
print("\nEdit config/gairi_head.yaml to change voice settings:")
print("  voice: 'gmw/en-us'  # or gmw/en, gmw/en-gb-x-rp")
print("  speed: 0.87         # 130 WPM (slower = less robotic)")
