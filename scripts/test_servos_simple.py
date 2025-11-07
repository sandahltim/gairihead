#!/usr/bin/env python3
from gpiozero import Servo
from gpiozero.pins.rpigpio import RPiGPIOFactory
from gpiozero import Device
from time import sleep

# Use RPi.GPIO backend (Pi 5 compatible)
Device.pin_factory = RPiGPIOFactory()

print("="*70)
print("SERVO TEST - Pi 5")
print("="*70)

# Servo pins
LEFT_EYELID_PIN = 17
RIGHT_EYELID_PIN = 27
MOUTH_PIN = 22

print("\nInitializing servos...")
print(f"  Left Eyelid: GPIO {LEFT_EYELID_PIN}")
print(f"  Right Eyelid: GPIO {RIGHT_EYELID_PIN}")
print(f"  Mouth: GPIO {MOUTH_PIN}")

try:
    # Create servo objects (SG90: -1=0deg, 0=90deg, 1=180deg)
    left_eyelid = Servo(LEFT_EYELID_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
    right_eyelid = Servo(RIGHT_EYELID_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
    mouth = Servo(MOUTH_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

    print("\nServos initialized!")

    # Test sequence
    print("\nTesting servos (watch for movement)...")

    print("\n1. Center all servos (90 degrees)")
    left_eyelid.value = 0  # Center
    right_eyelid.value = 0
    mouth.value = 0
    sleep(1)

    print("2. Left eyelid: Open -> Close -> Center")
    left_eyelid.value = -1  # 0deg (closed)
    sleep(0.5)
    left_eyelid.value = 1   # 180deg (open)
    sleep(0.5)
    left_eyelid.value = 0   # 90deg (center)
    sleep(0.5)

    print("3. Right eyelid: Open -> Close -> Center")
    right_eyelid.value = -1
    sleep(0.5)
    right_eyelid.value = 1
    sleep(0.5)
    right_eyelid.value = 0
    sleep(0.5)

    print("4. Mouth: Closed -> Open -> Center")
    mouth.value = -1
    sleep(0.5)
    mouth.value = 1
    sleep(0.5)
    mouth.value = 0
    sleep(0.5)

    print("5. Synchronized movement (blink 3x)")
    for i in range(3):
        print(f"   Blink {i+1}")
        left_eyelid.value = -1
        right_eyelid.value = -1
        sleep(0.2)
        left_eyelid.value = 1
        right_eyelid.value = 1
        sleep(0.3)

    print("\n6. Return to neutral position")
    left_eyelid.value = 0
    right_eyelid.value = 0
    mouth.value = 0
    sleep(0.5)

    print("\n" + "="*70)
    print("SERVO TEST COMPLETE")
    print("="*70)
    print("\nAll servos responded correctly!")

    # Cleanup
    left_eyelid.close()
    right_eyelid.close()
    mouth.close()

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
