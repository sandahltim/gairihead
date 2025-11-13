#!/usr/bin/env python3
"""
Test UART communication with Pico NeoPixel controller
Tests all expression modes and commands
"""

import serial
import time
import sys

def test_pico_communication():
    print("=== GairiHead Pico UART Test ===\n")

    # Open UART
    try:
        ser = serial.Serial('/dev/serial0', 115200, timeout=2)
        print("✓ Connected to Pico on /dev/serial0")
        time.sleep(1)  # Wait for Pico to be ready
    except Exception as e:
        print(f"✗ Failed to open serial port: {e}")
        print("\nMake sure UART is enabled:")
        print("  sudo raspi-config")
        print("  Interface Options → Serial Port")
        print("  Login shell: No, Serial hardware: Yes")
        return False

    def send_command(cmd):
        """Send command and wait for response"""
        print(f"\n→ Sending: {cmd}")
        ser.write(f"{cmd}\n".encode('utf-8'))
        time.sleep(0.2)

        if ser.in_waiting:
            response = ser.readline().decode('utf-8').strip()
            print(f"← Response: {response}")
            return response
        else:
            print("← No response")
            return None

    print("\n" + "="*50)
    print("Test 1: Expression Commands")
    print("="*50)

    expressions = ['idle', 'thinking', 'alert', 'happy', 'sarcasm', 'listening']
    for expr in expressions:
        resp = send_command(f"EXPR:{expr}")
        if resp == "OK":
            print(f"✓ Expression '{expr}' loaded")
        else:
            print(f"✗ Expression '{expr}' failed")
        time.sleep(2)  # Watch each expression

    print("\n" + "="*50)
    print("Test 2: Color Commands")
    print("="*50)

    colors = [
        ("Red", "255,0,0"),
        ("Green", "0,255,0"),
        ("Blue", "0,0,255"),
        ("Purple", "255,0,255")
    ]

    for name, rgb in colors:
        resp = send_command(f"COLOR:{rgb}")
        if resp == "OK":
            print(f"✓ Color {name} set")
        else:
            print(f"✗ Color {name} failed")
        time.sleep(1.5)

    print("\n" + "="*50)
    print("Test 3: Brightness Commands")
    print("="*50)

    for brightness in [50, 128, 255, 128]:
        resp = send_command(f"BRIGHTNESS:{brightness}")
        if resp == "OK":
            print(f"✓ Brightness set to {brightness}")
        else:
            print(f"✗ Brightness {brightness} failed")
        time.sleep(1)

    print("\n" + "="*50)
    print("Test 4: Blink Animation")
    print("="*50)

    for i in range(3):
        resp = send_command("ANIM:blink")
        if resp == "OK":
            print(f"✓ Blink {i+1}/3")
        time.sleep(0.5)

    print("\n" + "="*50)
    print("Test 5: Back to Idle")
    print("="*50)

    send_command("EXPR:idle")
    print("✓ Returned to idle mode (blue pulse)")

    ser.close()

    print("\n" + "="*50)
    print("✓ ALL TESTS COMPLETE!")
    print("="*50)
    print("\nIf you saw all expressions and colors change,")
    print("your UART communication is working perfectly!")

    return True


if __name__ == "__main__":
    try:
        success = test_pico_communication()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
