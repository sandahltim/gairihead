#!/usr/bin/env python3
"""
Test Arduino Emoji Display
Sends test messages to verify new emoji mappings
"""

import serial
import json
import time

# Test expressions with new emojis
test_expressions = [
    # New emotional expressions
    "sleeping",
    "speaking",
    "welcome",
    "error",
    "deep_focus",
    "diagnostic",

    # New animation types
    "pulse",
    "chase",
    "flash",
    "rainbow",
    "sparkle",
    "comet",
]

def test_emoji_display(port="/dev/ttyACM0", baudrate=115200):
    """Test emoji display with serial messages"""

    print(f"Connecting to Arduino at {port}...")

    try:
        # Open serial connection
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset

        print("Arduino connected! Testing emoji mappings...\n")

        for expr in test_expressions:
            # Create test message
            message = {
                "user": "Test User",
                "gairi": f"Testing expression: {expr}",
                "expression": expr,
                "user_auth": "tim",
                "auth_level": 1,
                "confidence": 0.95
            }

            # Send JSON message
            json_str = json.dumps(message)
            ser.write((json_str + "\n").encode())

            print(f"✓ Sent: {expr}")
            time.sleep(1.5)  # Pause between messages

        print("\n✅ Test complete! Check Arduino display for emojis.")
        print("Expected emojis:")
        print("  sleeping: z Z z")
        print("  speaking: o_o")
        print("  welcome: ^_^")
        print("  error: X_X")
        print("  deep_focus: @_@")
        print("  diagnostic: [?]")
        print("  pulse: ~")
        print("  chase: >>>")
        print("  flash: *")
        print("  rainbow: <3")
        print("  sparkle: ***")
        print("  comet: -->")

        ser.close()

    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        print("Make sure Arduino is connected at /dev/ttyACM0")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_emoji_display()
