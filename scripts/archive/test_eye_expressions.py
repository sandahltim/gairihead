#!/usr/bin/env python3
"""
Test Eye Expressions with Both Calibrated Servos
Tests various expressions using calibrated left and right eyelids
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
    # Inverted: -0.100 (closed) to 0.310 (open)
    return -0.100 + (normalized * 0.410)

def set_eyes(left_angle, right_angle, label=""):
    """Set both eyes to specific angles"""
    left_value = left_eye_angle_to_servo(left_angle)
    right_value = right_eye_angle_to_servo(right_angle)

    left_eyelid.value = left_value
    right_eyelid.value = right_value

    if label:
        print(f"  {label}")
        print(f"    Left: {left_angle}° → {left_value:+.3f}")
        print(f"    Right: {right_angle}° → {right_value:+.3f}")

def blink():
    """Perform a blink"""
    # Close
    set_eyes(0, 0, "Blink (closing)")
    time.sleep(0.15)
    # Open back to neutral
    set_eyes(55, 55, "Blink (opening)")

print("\n" + "="*70)
print("EYE EXPRESSION TEST - BOTH EYES CALIBRATED (SYMMETRIC)")
print("="*70)
print("\nTesting various expressions with both eyelids")
print("Left eye:  +0.100 (closed) to -0.310 (open)")
print("Right eye: -0.100 (closed) to +0.310 (open) [INVERTED]")
print("Both eyes use SAME range (0.410) for symmetric movement")
print("\n" + "="*70)

expressions = [
    # (left_angle, right_angle, name, hold_time)
    (55, 55, "NEUTRAL - Half Open", 3.0),
    (0, 0, "CLOSED - Both Eyes Shut", 2.0),
    (75, 75, "WIDE OPEN - Alert/Surprised", 2.0),
    (55, 55, "NEUTRAL - Back to Half", 2.0),
    (30, 30, "SLEEPY - Quarter Open", 2.5),
    (55, 55, "NEUTRAL - Waking Up", 2.0),
    (75, 30, "SKEPTICAL - Left Wide, Right Narrow", 2.5),
    (55, 55, "NEUTRAL - Reset", 2.0),
    (30, 75, "CURIOUS - Right Wide, Left Narrow", 2.5),
    (55, 55, "NEUTRAL - Reset", 2.0),
]

try:
    print("\nStarting expression sequence...\n")

    for left, right, name, duration in expressions:
        print(f"[{name}]")
        set_eyes(left, right, f"  Position: L={left}° R={right}°")
        time.sleep(duration)
        print()

    # Test blinking
    print("\n[BLINK TEST - 3 blinks]")
    for i in range(3):
        print(f"  Blink {i+1}/3")
        blink()
        time.sleep(0.5)

    print("\n[FINAL - Return to neutral]")
    set_eyes(55, 55, "  Neutral position")
    time.sleep(1.0)

    print("\n" + "="*70)
    print("Expression test complete!")
    print("="*70)
    print("\nObservations:")
    print("  - Did both eyes move smoothly?")
    print("  - Were the positions symmetrical when they should be?")
    print("  - Any twitching or instability?")
    print("  - Ready for mouth calibration? (y/n)")
    print("="*70 + "\n")

except KeyboardInterrupt:
    print("\n\nTest interrupted!")

finally:
    print("Returning to neutral and releasing servos...")
    set_eyes(55, 55)
    time.sleep(0.5)
    left_eyelid.close()
    right_eyelid.close()
    print("Done!\n")
