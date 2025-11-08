#!/usr/bin/env python3
"""
Test Microphone Recording

This script tests the microphone and saves a WAV file so you can hear what's being recorded.
"""

import sounddevice as sd
import numpy as np
import wave
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("MICROPHONE TEST")
print("="*70)
print("\nAvailable audio input devices:")
devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        default = " (DEFAULT)" if i == sd.default.device[0] else ""
        print(f"  [{i}] {dev['name']}{default}")
        print(f"      Channels: {dev['max_input_channels']} in")

print("\n" + "="*70)

# Use device 0 (EMEET) like GairiHead does
device_index = 0
sample_rate = 16000
duration = 5.0

print(f"\nRecording 5 seconds from device {device_index}...")
print("SPEAK NOW!")
print("="*70 + "\n")

try:
    # Record
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32,
        device=device_index
    )
    sd.wait()

    # Calculate RMS
    rms = np.sqrt(np.mean(recording ** 2))

    print(f"\n✅ Recording complete!")
    print(f"   RMS: {rms:.4f}")

    if rms < 0.01:
        print(f"   ⚠️  WARNING: Very low RMS! Microphone might not be working.")
        print(f"   Expected RMS for speech: 0.1 - 0.3")
    elif rms < 0.05:
        print(f"   ⚠️  Low RMS. Microphone volume might be too low.")
    else:
        print(f"   ✅ Good RMS level!")

    # Save to file
    output_file = "/tmp/gairihead_mic_test.wav"

    # Convert to int16 for WAV file
    audio_int16 = (recording * 32767).astype(np.int16)

    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    print(f"\n💾 Saved to: {output_file}")
    print("\nPlay it back with:")
    print(f"   aplay {output_file}")
    print("\nOr:")
    print(f"   aplay -D plughw:0,0 {output_file}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("DIAGNOSIS:")
print("="*70)

if rms < 0.01:
    print("\n❌ MICROPHONE NOT WORKING PROPERLY")
    print("\nPossible causes:")
    print("  1. Wrong microphone selected")
    print("  2. Microphone volume/gain too low")
    print("  3. Microphone muted")
    print("  4. USB microphone not recognized")
    print("\nTry:")
    print("  - Check microphone is plugged in")
    print("  - Run: alsamixer (adjust microphone volume)")
    print("  - Check USB connections")
elif rms < 0.05:
    print("\n⚠️  MICROPHONE VOLUME TOO LOW")
    print("\nTry:")
    print("  - Run: alsamixer")
    print("  - Increase 'Mic' or 'Capture' volume")
    print("  - Move closer to microphone")
else:
    print("\n✅ MICROPHONE WORKING!")
    print("\nIf Gary is still transcribing wrong content:")
    print("  - Gary server issue (not GairiHead)")
    print("  - Check Gary server logs")

print("="*70)
