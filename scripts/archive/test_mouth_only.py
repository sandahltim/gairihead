#!/usr/bin/env python3
"""
Test Mouth Servo Only
Simple test to verify mouth movements with calibrated values
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

# Calibrated mapping function
def mouth_angle_to_servo(angle):
    """Mouth: 0.000 (closed) to -0.600 (open)"""
    angle = max(0, min(60, angle))
    normalized = angle / 60.0
    return 0.000 - (normalized * 0.600)

def set_mouth(angle, label=""):
    """Set mouth to specific angle"""
    servo_value = mouth_angle_to_servo(angle)
    mouth.value = servo_value

    if label:
        print(f"  {label}")
    print(f"    Angle: {angle}° → Servo: {servo_value:+.3f}")

print("\n" + "="*70)
print("MOUTH SERVO TEST - GPIO 22")
print("="*70)
print("\nCALIBRATED RANGE:")
print("  0° (closed)   → servo  0.000")
print("  20° (partial) → servo -0.200")
print("  40° (more)    → servo -0.400")
print("  60° (open)    → servo -0.600")
print("\n" + "="*70)

# Test positions based on your calibration data
test_positions = [
    (0, "FULLY CLOSED", 3.0),
    (20, "PARTIAL OPEN", 3.0),
    (40, "MORE THAN PARTIAL", 3.0),
    (60, "FULLY OPEN", 3.0),
    (0, "BACK TO CLOSED", 2.0),
    (60, "BACK TO OPEN", 2.0),
    (10, "NEUTRAL (slight smile)", 2.0),
]

try:
    print("\nStarting mouth test sequence...\n")

    for angle, label, duration in test_positions:
        print(f"[{label}]")
        set_mouth(angle, label)
        time.sleep(duration)
        print()

    # Test rapid movement
    print("\n[RAPID MOVEMENT TEST - Talking simulation]")
    print("Moving between closed and partial open quickly...\n")
    for i in range(5):
        print(f"  Cycle {i+1}/5: Open")
        set_mouth(30)
        time.sleep(0.3)
        print(f"  Cycle {i+1}/5: Close")
        set_mouth(5)
        time.sleep(0.3)

    print("\n[RETURN TO NEUTRAL]")
    set_mouth(10, "Neutral/Slight Smile")
    time.sleep(1.5)

    print("\n" + "="*70)
    print("MOUTH TEST COMPLETE")
    print("="*70)
    print("\nObservations:")
    print("  - Did the mouth move at all positions?")
    print("  - Was the range adequate (0° to 60°)?")
    print("  - Any positions that didn't work?")
    print("  - Need to recalibrate? (y/n)")
    print("="*70 + "\n")

except KeyboardInterrupt:
    print("\n\nTest interrupted!")

finally:
    print("Returning to neutral and releasing servo...")
    set_mouth(10)
    time.sleep(0.5)
    mouth.close()
    print("Done!\n")
