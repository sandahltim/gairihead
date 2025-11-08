#!/usr/bin/env python3
"""
Hold mouth at specific position for servo horn adjustment
Usage: python3 hold_mouth_position.py [servo_value]
Default: 0.0 (neutral)
"""
import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import time
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use lgpio for Pi 5
Device.pin_factory = LGPIOFactory()

# Mouth servo on GPIO 22
mouth = Servo(
    22,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    frame_width=20/1000,
    pin_factory=Device.pin_factory
)

# Get position from command line or use neutral
if len(sys.argv) > 1:
    try:
        hold_value = float(sys.argv[1])
        if not -1.0 <= hold_value <= 1.0:
            print("Error: Value must be between -1.0 and 1.0")
            sys.exit(1)
    except ValueError:
        print("Error: Invalid number")
        sys.exit(1)
else:
    hold_value = 0.0

print("\n" + "="*70)
print(f"HOLDING MOUTH AT SERVO VALUE: {hold_value:+.3f}")
print("="*70)
print("\nThe servo is now holding position.")
print("\nYou can now:")
print("  1. Adjust the servo horn on the mechanism")
print("  2. Tighten the servo nut to lock it in place")
print("\nPress Ctrl+C when you're done to release the servo.")
print("="*70 + "\n")

mouth.value = hold_value
print(f"Holding at {hold_value:+.3f}... (Ctrl+C to stop)\n")

try:
    # Hold position indefinitely
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nReleasing servo...")

finally:
    mouth.close()
    print("Servo released. Done!\n")
