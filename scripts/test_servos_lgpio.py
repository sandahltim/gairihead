#!/usr/bin/env python3
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

# Use lgpio backend (Pi 5 native)
Device.pin_factory = LGPIOFactory()

print("="*70)
print("SERVO TEST - Pi 5 with lgpio")
print("="*70)

# Servo pins
LEFT_EYELID_PIN = 17
RIGHT_EYELID_PIN = 27
MOUTH_PIN = 22

print("\nInitializing servos...")
print(f"  Left Eyelid: GPIO {LEFT_EYELID_PIN}")
print(f"  Right Eyelid: GPIO {RIGHT_EYELID_PIN}")
print(f"  Mouth: GPIO {MOUTH_PIN}")
print(f"  Pin factory: {Device.pin_factory}")

try:
    # Create servo objects (SG90: min=500us, max=2500us)
    left_eyelid = Servo(LEFT_EYELID_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
    right_eyelid = Servo(RIGHT_EYELID_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
    mouth = Servo(MOUTH_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

    print("\nServos initialized successfully!")

    # Test sequence
    print("\nTesting servos (watch for movement)...")

    print("\n1. Center all servos (90 degrees)")
    left_eyelid.mid()
    right_eyelid.mid()
    mouth.mid()
    sleep(1)

    print("2. Left eyelid sweep")
    print("   Min (0 deg)")
    left_eyelid.min()
    sleep(0.5)
    print("   Mid (90 deg)")
    left_eyelid.mid()
    sleep(0.5)
    print("   Max (180 deg)")
    left_eyelid.max()
    sleep(0.5)
    print("   Mid (90 deg)")
    left_eyelid.mid()
    sleep(0.5)

    print("3. Right eyelid sweep")
    right_eyelid.min()
    sleep(0.5)
    right_eyelid.mid()
    sleep(0.5)
    right_eyelid.max()
    sleep(0.5)
    right_eyelid.mid()
    sleep(0.5)

    print("4. Mouth sweep")
    mouth.min()
    sleep(0.5)
    mouth.mid()
    sleep(0.5)
    mouth.max()
    sleep(0.5)
    mouth.mid()
    sleep(0.5)

    print("5. Synchronized blink (3x)")
    for i in range(3):
        print(f"   Blink {i+1}")
        left_eyelid.min()
        right_eyelid.min()
        sleep(0.15)
        left_eyelid.max()
        right_eyelid.max()
        sleep(0.3)

    print("6. Expression test - Happy")
    left_eyelid.value = 0.5  # 135 deg (slightly open)
    right_eyelid.value = 0.5
    mouth.value = 0.8        # 162 deg (big smile)
    sleep(1)

    print("7. Expression test - Thinking")
    left_eyelid.value = -0.5  # 45 deg (squinting)
    right_eyelid.value = -0.5
    mouth.value = -0.5       # 45 deg (neutral/frown)
    sleep(1)

    print("\n8. Return to neutral")
    left_eyelid.mid()
    right_eyelid.mid()
    mouth.mid()
    sleep(0.5)

    print("\n" + "="*70)
    print("SERVO TEST COMPLETE!")
    print("="*70)
    print("\nDid all servos move correctly? (Y/n)")
    print("- Left eyelid moved through full range?")
    print("- Right eyelid moved through full range?")
    print("- Mouth moved through full range?")

    # Cleanup
    left_eyelid.close()
    right_eyelid.close()
    mouth.close()

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
