#!/usr/bin/env python3
"""
Test All Servos - Eyes + Mouth
Comprehensive test of all calibrated servos with various expressions
"""
import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import time
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use lgpio for Pi 5
Device.pin_factory = LGPIOFactory()

# Initialize all servos
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

mouth = Servo(
    22,
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

def mouth_angle_to_servo(angle):
    """Mouth: 0.000 (closed) to -0.600 (open)"""
    angle = max(0, min(60, angle))
    normalized = angle / 60.0
    return 0.000 - (normalized * 0.600)

def set_servos(left_eye, right_eye, mouth_angle, label=""):
    """Set all servos to specific angles"""
    left_value = left_eye_angle_to_servo(left_eye)
    right_value = right_eye_angle_to_servo(right_eye)
    mouth_value = mouth_angle_to_servo(mouth_angle)

    left_eyelid.value = left_value
    right_eyelid.value = right_value
    mouth.value = mouth_value

    if label:
        print(f"  {label}")
        print(f"    Eyes: L={left_eye}° R={right_eye}° | Mouth: {mouth_angle}°")

def blink():
    """Perform a blink (keep mouth position)"""
    # Store current mouth position
    current_mouth = 10

    # Close eyes
    set_servos(0, 0, current_mouth)
    time.sleep(0.15)
    # Open back to neutral
    set_servos(55, 55, current_mouth)

print("\n" + "="*70)
print("FULL SERVO SYSTEM TEST - EYES + MOUTH")
print("="*70)
print("\nCALIBRATED RANGES:")
print("  Left eye:  +0.100 (closed) to -0.310 (open) | 0-75°")
print("  Right eye: -0.100 (closed) to +0.310 (open) | 0-75°")
print("  Mouth:      0.000 (closed) to -0.600 (open) | 0-60°")
print("\n" + "="*70)

# Expression test sequence
expressions = [
    # (left_eye, right_eye, mouth, name, hold_time)
    (55, 55, 10, "IDLE - Neutral with slight smile", 3.0),
    (75, 75, 0, "ALERT - Wide eyes, closed mouth", 2.5),
    (55, 55, 10, "Back to neutral", 1.5),
    (55, 55, 30, "SPEAKING - Normal eyes, mouth open", 2.5),
    (55, 55, 10, "Back to neutral", 1.5),
    (75, 75, 40, "SURPRISED - Wide eyes, mouth open wide", 2.5),
    (55, 55, 10, "Back to neutral", 1.5),
    (30, 30, 5, "SLEEPY/TIRED - Half-closed eyes, barely open mouth", 2.5),
    (55, 55, 10, "WAKING UP - Back to neutral", 2.0),
    (75, 30, 0, "SKEPTICAL - Left eye wide, right squint, mouth closed", 2.5),
    (55, 55, 10, "Back to neutral", 1.5),
    (55, 55, 50, "EXCITED TALKING - Normal eyes, mouth wide", 2.5),
    (55, 55, 10, "Back to neutral", 1.5),
    (0, 0, 0, "FULLY CLOSED - All servos at minimum", 2.0),
    (55, 55, 10, "RESET - Back to idle", 2.0),
]

try:
    print("\nStarting expression sequence...\n")

    for left, right, mouth_pos, name, duration in expressions:
        print(f"[{name}]")
        set_servos(left, right, mouth_pos)
        time.sleep(duration)
        print()

    # Test blinking
    print("\n[BLINK TEST - 3 blinks while maintaining neutral]")
    for i in range(3):
        print(f"  Blink {i+1}/3")
        blink()
        time.sleep(0.5)

    print("\n[FINAL - Return to idle]")
    set_servos(55, 55, 10, "  Idle position (neutral eyes, slight smile)")
    time.sleep(1.5)

    print("\n" + "="*70)
    print("FULL SERVO TEST COMPLETE!")
    print("="*70)
    print("\nAll three servos are calibrated and functioning.")
    print("\nNext steps:")
    print("  - Integrate with expression system")
    print("  - Test with NeoPixel eyes (when Pico 2 arrives)")
    print("  - Connect to voice/face recognition pipeline")
    print("="*70 + "\n")

except KeyboardInterrupt:
    print("\n\nTest interrupted!")

finally:
    print("Returning to idle and releasing servos...")
    set_servos(55, 55, 10)
    time.sleep(0.5)
    left_eyelid.close()
    right_eyelid.close()
    mouth.close()
    print("Done!\n")
