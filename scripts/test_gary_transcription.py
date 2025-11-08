#!/usr/bin/env python3
"""
Test Gary Server OPTIMIZED Voice Pipeline
Tests the new single-call process_audio_query() flow (transcription + LLM in one call)
"""

import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import yaml
import time
import sounddevice as sd
import numpy as np
from llm_tier_manager import LLMTierManager
from loguru import logger

def load_config():
    """Load GairiHead config"""
    with open('/home/tim/GairiHead/config/gairi_head.yaml', 'r') as f:
        return yaml.safe_load(f)

def record_test_audio(duration=3.0, sample_rate=16000):
    """Record test audio"""
    logger.info(f"🎤 Recording {duration}s of audio...")
    logger.info("   Speak now!")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()

    audio = audio.flatten()
    rms = np.sqrt(np.mean(audio**2))
    logger.success(f"✅ Recorded audio (RMS: {rms:.4f})")

    return audio

def main():
    """Test Gary optimized pipeline"""
    print("\n" + "="*70)
    print("GARY OPTIMIZED VOICE PIPELINE TEST")
    print("="*70)
    print("\nThis tests the NEW single-call process_audio_query() flow")
    print("OLD: Record → Transcribe (call 1) → Query LLM (call 2) → Speak")
    print("NEW: Record → Process Full Pipeline (call 1) → Speak")
    print("\nMake sure Gary server is running at ws://100.106.44.11:8765/ws")
    print("="*70 + "\n")

    # Load config
    config = load_config()

    # Create LLM manager (handles Gary connection)
    llm_manager = LLMTierManager(config)

    # Record test audio
    audio = record_test_audio(duration=3.0)

    # Test 1: OLD FLOW - Transcribe only (for comparison)
    print("\n" + "-"*70)
    print("TEST 1: OLD FLOW - Transcription only (for comparison)")
    print("-"*70)

    start_time = time.time()
    try:
        text = llm_manager.transcribe_audio(audio, sample_rate=16000)
        elapsed_old = int((time.time() - start_time) * 1000)

        if text:
            print(f"\n✅ Transcription SUCCESS!")
            print(f"   Text: \"{text}\"")
            print(f"   Time: {elapsed_old}ms")
        else:
            print(f"\n❌ FAILED - No transcription returned")
            elapsed_old = None
    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        elapsed_old = None

    # Test 2: NEW FLOW - Single-call optimized (transcription + LLM)
    print("\n" + "-"*70)
    print("TEST 2: NEW FLOW - Optimized single-call (transcription + LLM)")
    print("-"*70)

    authorization = {
        'level': 1,
        'user': 'tim',
        'confidence': 0.95
    }

    start_time = time.time()
    try:
        result = llm_manager.process_audio_query(audio, sample_rate=16000, authorization=authorization)
        elapsed_new = int((time.time() - start_time) * 1000)

        if result and result.get('response'):
            print(f"\n✅ OPTIMIZED PIPELINE SUCCESS!")
            print(f"   Transcription: \"{result.get('transcription', 'N/A')}\"")
            print(f"   Response: \"{result['response'][:100]}{'...' if len(result['response']) > 100 else ''}\"")
            print(f"   Tier: {result.get('tier', 'unknown')}")
            print(f"   Time: {elapsed_new}ms")
        else:
            print(f"\n❌ FAILED - No response returned")
            print(f"   Result: {result}")
            elapsed_new = None
    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        import traceback
        traceback.print_exc()
        elapsed_new = None

    # Test 3: Measure savings
    if elapsed_old and elapsed_new:
        print("\n" + "-"*70)
        print("TEST 3: Performance Comparison")
        print("-"*70)

        # OLD flow would be: transcribe + query (estimate query at 50-100ms)
        estimated_old_total = elapsed_old + 75  # Transcribe + estimated query time
        savings = estimated_old_total - elapsed_new

        print(f"\n⏱️  OLD FLOW (2 calls):")
        print(f"   Transcribe: {elapsed_old}ms")
        print(f"   Query: ~75ms (estimated)")
        print(f"   Total: ~{estimated_old_total}ms")
        print(f"\n⚡ NEW FLOW (1 call):")
        print(f"   Combined: {elapsed_new}ms")
        print(f"\n💡 Savings: ~{savings}ms ({savings/estimated_old_total*100:.1f}% faster)")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    if elapsed_new:
        print("✅ Optimized pipeline is WORKING!")
        print(f"🚀 Response time: {elapsed_new}ms")
        if elapsed_new < 2000:
            print(f"   EXCELLENT - Under 2 seconds!")
        elif elapsed_new < 5000:
            print(f"   GOOD - Under 5 seconds")
        else:
            print(f"   ⚠️  Slower than expected")
    else:
        print("❌ Optimized pipeline FAILED")
        print("   Troubleshooting:")
        print("   1. Is Gary server running? (python3 /Gary/src/api_server.py)")
        print("   2. Is WebSocket listening on port 8765?")
        print("   3. Did Gary implement process_full_pipeline support?")
        print("   4. Check Gary logs for errors")

    print("="*70 + "\n")

if __name__ == "__main__":
    main()
