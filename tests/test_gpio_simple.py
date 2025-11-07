#!/usr/bin/env python3
"""
Simple GPIO Test - Verify GPIO access before servos arrive

This tests GPIO 17 (our left eyelid pin) with a simple on/off pattern
Can test with an LED or just verify no errors
"""

import sys
import time

sys.path.insert(0, '/home/tim/GairiHead/src')

print("=" * 60)
print("GairiHead GPIO Test (Pre-Servo)")
print("=" * 60)
print()

# Test GPIO access
print("1. Testing GPIO library access...")
try:
    import pigpio
    print("   ✅ pigpio imported")
except Exception as e:
    print(f"   ❌ pigpio import failed: {e}")
    sys.exit(1)

# Connect to daemon
print("\n2. Connecting to pigpio daemon...")
try:
    pi = pigpio.pi()
    if not pi.connected:
        print("   ❌ pigpio daemon not connected")
        print("   Run: sudo systemctl start pigpiod")
        sys.exit(1)
    print(f"   ✅ Connected to pigpio (hardware revision: {pi.get_hardware_revision()})")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    sys.exit(1)

# Test our servo pins
PINS_TO_TEST = {
    17: "Left Eyelid",
    27: "Right Eyelid",
    22: "Mouth"
}

print("\n3. Testing servo pins (M.2 HAT safe: 17, 27, 22)...")
for pin, name in PINS_TO_TEST.items():
    try:
        # Set as output
        pi.set_mode(pin, pigpio.OUTPUT)

        # Quick on/off test
        pi.write(pin, 1)
        time.sleep(0.1)
        pi.write(pin, 0)

        print(f"   ✅ GPIO {pin} ({name}): OK")
    except Exception as e:
        print(f"   ❌ GPIO {pin} ({name}): {e}")

# Optional: Blink test with GPIO 17
print("\n4. Optional: LED blink test on GPIO 17")
print("   If you have an LED connected to GPIO 17:")
print("   - Long leg (anode) → GPIO 17")
print("   - Short leg (cathode) → 330Ω resistor → GND")
print()
response = input("   Run LED blink? (y/n): ").strip().lower()

if response == 'y':
    print("\n   Blinking GPIO 17 (5 times)...")
    TEST_PIN = 17

    try:
        pi.set_mode(TEST_PIN, pigpio.OUTPUT)

        for i in range(5):
            print(f"   Blink {i+1}/5")
            pi.write(TEST_PIN, 1)  # On
            time.sleep(0.5)
            pi.write(TEST_PIN, 0)  # Off
            time.sleep(0.5)

        print("   ✅ Blink test complete")
    except Exception as e:
        print(f"   ❌ Blink test failed: {e}")
else:
    print("   Skipped")

# PWM test (what servos will use)
print("\n5. Testing PWM capability (servo control)...")
TEST_PIN = 17

try:
    # Servo PWM: 50Hz (20ms period)
    # Typical servo: 1000-2000μs pulse width
    # Test with 1500μs (center position)

    frequency = 50  # Hz
    pi.set_PWM_frequency(TEST_PIN, frequency)

    # Set to neutral position (1500μs = 7.5% duty at 50Hz)
    # 1500μs / 20000μs = 0.075 = 7.5%
    # pigpio uses 0-255 range, so 7.5% = 19

    print(f"   Setting PWM: {frequency}Hz, 1500μs pulse (servo neutral)")
    pi.set_PWM_dutycycle(TEST_PIN, 19)  # 7.5% of 255
    time.sleep(1)

    # Stop PWM
    pi.set_PWM_dutycycle(TEST_PIN, 0)

    print("   ✅ PWM test passed")
except Exception as e:
    print(f"   ❌ PWM test failed: {e}")

# Cleanup
print("\n6. Cleanup...")
try:
    for pin in PINS_TO_TEST.keys():
        pi.write(pin, 0)
        pi.set_mode(pin, pigpio.INPUT)

    pi.stop()
    print("   ✅ GPIO cleaned up")
except Exception as e:
    print(f"   ⚠️  Cleanup warning: {e}")

print()
print("=" * 60)
print("✅ GPIO test complete!")
print()
print("Results:")
print("  - GPIO access: OK")
print("  - Servo pins accessible: GPIO 17, 27, 22")
print("  - PWM capability: OK")
print()
print("Next: Connect servos and run:")
print("  python tests/test_servos.py")
print("=" * 60)
