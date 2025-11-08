#!/usr/bin/env python3
"""
Hold both eyes at WIDE OPEN position for servo horn adjustment
Press Ctrl+C when done securing the servo nuts
"""
import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import time
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use lgpio for Pi 5
Device.pin_factory = LGPIOFactory()

# Initialize both servos
left_eyelid = Servo(
    17,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    frame_width=20/1000,
    pin_factory=Device.pin_factory
)

right_eyelid = Servo(
    27,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    frame_width=20/1000,
    pin_factory=Device.pin_factory
)

# Calibrated mapping functions
def left_eye_angle_to_servo(angle):
    """Left eye: 0.100 (closed) to -0.310 (open)"""
    angle = max(0, min(75, angle))
    normalized = angle / 75.0
    return 0.100 - (normalized * 0.410)

def right_eye_angle_to_servo(angle):
    """Right eye: INVERTED left eye for symmetric movement"""
    angle = max(0, min(75, angle))
    normalized = angle / 75.0
    return -0.100 + (normalized * 0.410)

print("\n" + "="*70)
print("HOLDING EYES AT WIDE OPEN (75°)")
print("="*70)
print("\nBoth servos are now holding at fully open position.")
print("\nYou can now:")
print("  1. Adjust the servo horn on the mechanism")
print("  2. Tighten the servo nut to lock it in place")
print("  3. Ensure the eyelid is at maximum open position")
print("\nPress Ctrl+C when you're done to release the servos.")
print("="*70 + "\n")

# Set to wide open (75°)
left_value = left_eye_angle_to_servo(75)
right_value = right_eye_angle_to_servo(75)

left_eyelid.value = left_value
right_eyelid.value = right_value

print(f"Left eye:  75° → servo {left_value:+.3f}")
print(f"Right eye: 75° → servo {right_value:+.3f}")
print("\nHolding position... (Ctrl+C to stop)\n")

try:
    # Hold position indefinitely
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nReleasing servos...")

finally:
    left_eyelid.close()
    right_eyelid.close()
    print("Servos released. Done!\n")
