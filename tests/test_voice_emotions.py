#!/usr/bin/env python3
"""
Test script for emotion-based voice modulation
Tests different emotions with the same text to demonstrate voice changes
"""

import sys
import yaml
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from voice_handler import VoiceHandler

def main():
    """Test emotion-based voice modulation with various emotional states"""

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    print("=" * 70)
    print("VOICE EMOTION MODULATION TEST")
    print("=" * 70)
    print()

    # Load config
    config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize voice handler
    print("Initializing VoiceHandler...")
    voice_handler = VoiceHandler(config)
    print()

    # Test phrase
    test_phrase = "That's a terrible plan. I'm in."

    # Test emotions to demonstrate
    test_emotions = [
        ('idle', 'Baseline (neutral voice)'),
        ('happy', 'Positive - faster, brighter'),
        ('sarcasm', 'Deadpan delivery - slower, lower'),
        ('frustrated', 'Annoyed - slow, loud, lower'),
        ('celebration', 'Excited - fast, higher pitch'),
        ('bored', 'Disinterested - slow, quiet'),
        ('surprised', 'Shocked - fast, high pitch'),
        ('deadpan', 'TARS mode - flat delivery'),
    ]

    print(f"Test phrase: \"{test_phrase}\"\n")
    print("=" * 70)

    for emotion, description in test_emotions:
        print(f"\n{emotion.upper()}")
        print(f"  Description: {description}")
        print(f"  Speaking...")

        success = voice_handler.speak(test_phrase, emotion=emotion)

        if success:
            print(f"  ✅ Success")
        else:
            print(f"  ❌ Failed")

        # Brief pause between emotions
        import time
        time.sleep(1.0)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    # Show stats
    stats = voice_handler.get_stats()
    print(f"\nStatistics:")
    print(f"  TTS successes: {stats['tts_successes']}")
    print(f"  TTS failures: {stats['tts_failures']}")

    print("\n✅ Voice emotion modulation test complete\n")


if __name__ == '__main__':
    main()
