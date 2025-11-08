#!/usr/bin/env python3
"""
Left Eyelid Servo Calibration Script
Interactive calibration for left eye servo on GPIO 17

Use this to test positions while adjusting the physical mechanism.
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

def angle_to_servo_value(angle, min_angle=0, max_angle=75):
    """Convert angle (0-75) to servo value - CALIBRATED for left eye mechanism"""
    # Physical calibration:
    # 0° (closed) → servo -0.7
    # 75° (open)  → servo -1.0
    normalized = (angle - min_angle) / (max_angle - min_angle)
    # Map to actual working range: -0.7 (closed) to -1.0 (open)
    return -0.7 - (normalized * 0.3)

def set_angle(angle):
    """Set servo to specific angle"""
    servo_value = angle_to_servo_value(angle)
    left_eyelid.value = servo_value
    print(f"  → Servo value: {servo_value:.3f}")

# Calibration positions (physical limit is 0-75°)
positions = [
    (0, "Fully Closed (MIN)"),
    (10, "Almost Closed"),
    (20, "Slightly Open"),
    (30, "Quarter Open"),
    (40, "Neutral/Half Open"),
    (55, "Three-Quarter Open"),
    (65, "Nearly Wide"),
    (75, "Fully Wide Open (MAX)")
]

print("\n" + "="*60)
print("LEFT EYELID SERVO CALIBRATION")
print("="*60)
print("\nServo: GPIO 17 (Left Eyelid)")
print("Range: 0° (closed) to 75° (wide open) - PHYSICAL LIMIT")
print("Neutral: 40°")
print("\nCommands:")
print("  n = Next position")
print("  p = Previous position")
print("  r = Repeat current position")
print("  j = Jump to specific angle (0-75)")
print("  q = Quit")
print("="*60)

# Start at neutral
current_idx = 4  # Start at 40° neutral
set_angle(positions[current_idx][0])
print(f"\n[{current_idx+1}/{len(positions)}] {positions[current_idx][0]}° - {positions[current_idx][1]}")

try:
    while True:
        command = input("\nCommand [n/p/r/j/q]: ").strip().lower()

        if command == 'q':
            print("\nReturning to neutral before exit...")
            set_angle(40)
            time.sleep(0.5)
            break

        elif command == 'n':
            if current_idx < len(positions) - 1:
                current_idx += 1
                angle, desc = positions[current_idx]
                print(f"\n[{current_idx+1}/{len(positions)}] {angle}° - {desc}")
                set_angle(angle)
            else:
                print("  Already at last position!")

        elif command == 'p':
            if current_idx > 0:
                current_idx -= 1
                angle, desc = positions[current_idx]
                print(f"\n[{current_idx+1}/{len(positions)}] {angle}° - {desc}")
                set_angle(angle)
            else:
                print("  Already at first position!")

        elif command == 'r':
            angle, desc = positions[current_idx]
            print(f"\n[{current_idx+1}/{len(positions)}] {angle}° - {desc} (repeated)")
            set_angle(angle)

        elif command == 'j':
            try:
                angle = int(input("Enter angle (0-75): "))
                if 0 <= angle <= 75:
                    print(f"\nJumping to {angle}°")
                    set_angle(angle)
                else:
                    print("  Angle must be between 0 and 75!")
            except ValueError:
                print("  Invalid number!")

        elif command == '':
            # Empty enter = next
            if current_idx < len(positions) - 1:
                current_idx += 1
                angle, desc = positions[current_idx]
                print(f"\n[{current_idx+1}/{len(positions)}] {angle}° - {desc}")
                set_angle(angle)
            else:
                print("  Already at last position!")
        else:
            print("  Unknown command!")

except KeyboardInterrupt:
    print("\n\nInterrupted! Returning to neutral...")
    set_angle(40)
    time.sleep(0.5)

finally:
    print("\nCleaning up GPIO...")
    left_eyelid.close()
    print("Done!")
