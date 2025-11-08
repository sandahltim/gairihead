#!/usr/bin/env python3
"""
Precise Servo Calibration Tool
Fine-tune servo position using raw values and save calibration data
"""
import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

import time
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use lgpio for Pi 5 compatibility
Device.pin_factory = LGPIOFactory()

# Left eyelid servo on GPIO 17
left_eyelid = Servo(
    17,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    frame_width=20/1000,
    pin_factory=Device.pin_factory
)

print("\n" + "="*70)
print("PRECISE SERVO CALIBRATION - LEFT EYELID (GPIO 17)")
print("="*70)
print("\nThis tool helps you find the exact servo range for your mechanism.")
print("\nServo values range from -1.0 (min) to +1.0 (max)")
print("You'll test different values to find what works for your eyelid.")
print("\n" + "="*70)

# Start at neutral (0.0)
current_value = 0.0
left_eyelid.value = current_value

saved_positions = {}

print(f"\nStarting at servo value: {current_value:.2f}")
print("\nCOMMANDS:")
print("  +  = Increase by 0.1")
print("  ++ = Increase by 0.01 (fine tune)")
print("  -  = Decrease by 0.1")
print("  -- = Decrease by 0.01 (fine tune)")
print("  s  = Save current position with a label")
print("  v  = View saved positions")
print("  g  = Go to specific value (-1.0 to 1.0)")
print("  h  = Show this help")
print("  q  = Quit")
print("="*70)

try:
    while True:
        print(f"\nCurrent servo value: {current_value:.3f} | Command: ", end='')
        command = input().strip().lower()

        if command == 'q':
            print("\nQuitting...")
            break

        elif command == '+':
            current_value = min(1.0, current_value + 0.1)
            left_eyelid.value = current_value
            print(f"  → Moved to {current_value:.3f}")

        elif command == '++':
            current_value = min(1.0, current_value + 0.01)
            left_eyelid.value = current_value
            print(f"  → Moved to {current_value:.3f}")

        elif command == '-':
            current_value = max(-1.0, current_value - 0.1)
            left_eyelid.value = current_value
            print(f"  → Moved to {current_value:.3f}")

        elif command == '--':
            current_value = max(-1.0, current_value - 0.01)
            left_eyelid.value = current_value
            print(f"  → Moved to {current_value:.3f}")

        elif command == 's':
            label = input("  Enter label for this position: ").strip()
            if label:
                saved_positions[label] = current_value
                print(f"  ✓ Saved '{label}' at {current_value:.3f}")
            else:
                print("  ✗ Label cannot be empty")

        elif command == 'v':
            if saved_positions:
                print("\n  SAVED POSITIONS:")
                for label, value in saved_positions.items():
                    print(f"    {label}: {value:.3f}")
            else:
                print("  No positions saved yet")

        elif command == 'g':
            try:
                new_value = float(input("  Enter value (-1.0 to 1.0): "))
                if -1.0 <= new_value <= 1.0:
                    current_value = new_value
                    left_eyelid.value = current_value
                    print(f"  → Moved to {current_value:.3f}")
                else:
                    print("  ✗ Value must be between -1.0 and 1.0")
            except ValueError:
                print("  ✗ Invalid number")

        elif command == 'h':
            print("\n  COMMANDS:")
            print("    +  = Increase by 0.1")
            print("    ++ = Increase by 0.01 (fine tune)")
            print("    -  = Decrease by 0.1")
            print("    -- = Decrease by 0.01 (fine tune)")
            print("    s  = Save current position")
            print("    v  = View saved positions")
            print("    g  = Go to specific value")
            print("    h  = Show this help")
            print("    q  = Quit")

        elif command == '':
            # Just Enter - repeat current position
            left_eyelid.value = current_value
            print(f"  → Position repeated at {current_value:.3f}")

        else:
            print(f"  ✗ Unknown command '{command}' - type 'h' for help")

except KeyboardInterrupt:
    print("\n\nInterrupted!")

finally:
    print("\nReturning to neutral (0.0)...")
    left_eyelid.value = 0.0
    time.sleep(0.3)

    if saved_positions:
        print("\n" + "="*70)
        print("CALIBRATION SUMMARY")
        print("="*70)
        for label, value in saved_positions.items():
            print(f"  {label}: {value:.3f}")
        print("="*70)

        # Write to file
        with open('/home/tim/GairiHead/left_eye_calibration.txt', 'w') as f:
            f.write("LEFT EYE SERVO CALIBRATION DATA\n")
            f.write("="*70 + "\n\n")
            for label, value in saved_positions.items():
                f.write(f"{label}: {value:.3f}\n")
        print("\n✓ Calibration data saved to: /home/tim/GairiHead/left_eye_calibration.txt")

    left_eyelid.close()
    print("\nServo released. Done!\n")
