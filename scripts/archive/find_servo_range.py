#!/usr/bin/env python3
"""
Find the actual working range of the left eyelid servo
Tests different servo values to find min/max positions
"""

import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import time
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use lgpio for Pi 5
Device.pin_factory = LGPIOFactory()

# Initialize left eyelid servo (GPIO 17)
print("Initializing left eyelid servo on GPIO 17...")
left_eyelid = Servo(
    17,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    pin_factory=Device.pin_factory
)

print("\n" + "="*60)
print("SERVO RANGE FINDER")
print("="*60)
print("\nThis will test raw servo values from -1.0 to 1.0")
print("Watch the servo and note when it reaches:")
print("  - Fully closed position")
print("  - Fully open position")
print("\nWe'll move in increments of 0.1")
print("="*60)

# Test values from -1.0 to 1.0
test_values = []
for i in range(-10, 11):
    test_values.append(i / 10.0)

try:
    for value in test_values:
        left_eyelid.value = value
        input(f"\nServo value: {value:+.1f}  |  Press Enter for next (or Ctrl+C to stop)...")

except KeyboardInterrupt:
    print("\n\nStopped!")

finally:
    print("\nReturning to middle position (0.0)...")
    left_eyelid.value = 0.0
    time.sleep(0.5)
    print("Cleaning up GPIO...")
    left_eyelid.close()
    print("\n" + "="*60)
    print("Based on what you observed, what servo values corresponded to:")
    print("  - Fully CLOSED?")
    print("  - Fully OPEN?")
    print("="*60)
    print("Done!")
