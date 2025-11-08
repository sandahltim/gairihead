#!/usr/bin/env python3
"""
Test the calibrated left eye servo
Runs through key positions using the calibrated servo controller
"""
import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import time
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use lgpio for Pi 5
Device.pin_factory = LGPIOFactory()

# Import the calibrated function from servo_controller
from servo_controller import ServoController

print("\n" + "="*70)
print("TESTING CALIBRATED LEFT EYE SERVO")
print("="*70)
print("\nThis will test the left eyelid using calibrated values:")
print("  - 0° (fully closed) → servo 0.100")
print("  - 55° (half open)   → servo -0.200")
print("  - 75° (fully open)  → servo -0.310")
print("\n" + "="*70)

# Create a simple test using just the left eye servo
left_eyelid = Servo(
    17,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    frame_width=20/1000,
    pin_factory=Device.pin_factory
)

def angle_to_servo_value_left_eye(angle):
    """CALIBRATED mapping for left eyelid"""
    angle = max(0, min(75, angle))
    normalized = angle / 75.0
    servo_value = 0.100 - (normalized * 0.410)
    return servo_value

# Test positions
test_positions = [
    (0, "Fully Closed"),
    (20, "Slightly Open"),
    (37, "True Half (geometric)"),
    (55, "Half Open (calibrated neutral)"),
    (65, "Nearly Wide"),
    (75, "Fully Open"),
]

try:
    print("\nStarting test sequence (3 second delay between positions)...\n")

    for angle, description in test_positions:
        servo_value = angle_to_servo_value_left_eye(angle)
        left_eyelid.value = servo_value

        print(f"  {angle:3d}° - {description:30s} → servo {servo_value:+.3f}")
        time.sleep(3.0)

    print("\nTest complete! Returning to neutral (55°)...")
    left_eyelid.value = angle_to_servo_value_left_eye(55)
    time.sleep(1.0)

    print("\n" + "="*70)
    print("Did the eyelid move smoothly through all positions? (y/n): ", end='')
    response = input().strip().lower()

    if response == 'y':
        print("\n✓ Calibration successful!")
        print("  Left eye is ready for integration with full expressions.")
    else:
        print("\n⚠ If positions were off, you may need to re-run:")
        print("  python3 scripts/precise_servo_calibration.py")
    print("="*70)

except KeyboardInterrupt:
    print("\n\nTest interrupted!")

finally:
    print("\nReturning to neutral and releasing servo...")
    left_eyelid.value = angle_to_servo_value_left_eye(55)
    time.sleep(0.5)
    left_eyelid.close()
    print("Done!\n")
